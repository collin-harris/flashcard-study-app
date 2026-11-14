import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.deck import Deck
from app.schemas.generation import (
    GeneratedCard,
    GenerateRejected,
    GenerateRequest,
    GenerateResponse,
    GenerateSuccess,
    GenerationRemaining,
)
from app.routers.auth import get_db, get_current_user
from app.services.card_generation import CardGenerationError, CardGenerationSetupError, generate_cards
from app.services.generation_limits import (
    GenerationLimitReached,
    record_outcome,
    remaining_generations,
    reserve_generation,
    user_limit,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# This endpoint's own settings; the eval keeps card_generation's defaults.
# The timeout applies to each attempt, not the call as a whole.
GENERATE_TIMEOUT_SECONDS = 45
GENERATE_MAX_RETRIES = 1

RETRY_MESSAGE = "Couldn't generate cards. Please try again."


def _limit_message(error: GenerationLimitReached) -> str:
    if error.scope == "user":
        return f"You've used all {error.limit} of your card generations for the last 24 hours. Please try again later."
    if error.scope == "demo":
        return (
            f"The shared demo account has used all {error.limit} of its card generations "
            "for the last 24 hours. Please try again later."
        )
    return "Card generation has reached its overall limit for the last 24 hours. Please try again later."


@router.post("/decks/{deck_id}/cards/generate", response_model=GenerateResponse)
def generate_deck_cards(
    deck_id: int,
    generate_data: GenerateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Reserve a counted row before calling the API
    try:
        reservation = reserve_generation(db, current_user, len(generate_data.notes))
    except GenerationLimitReached as e:
        raise HTTPException(status_code=429, detail=_limit_message(e))
    generation_id = reservation.generation_id

    # Logs carry the row id and the kind of failure, never an error's message:
    # a message can quote the model's output, which quotes the notes
    try:
        result = generate_cards(
            generate_data.notes, timeout=GENERATE_TIMEOUT_SECONDS, max_retries=GENERATE_MAX_RETRIES
        )
    except CardGenerationError as e:
        record_outcome(db, reservation, e.kind, e.metadata)
        if e.kind == "api_error":
            cause = e.__cause__
            logger.warning(
                "Generation %s failed: api_error (%s, status %s)",
                generation_id, type(cause).__name__, getattr(cause, "status_code", None),
            )
            raise HTTPException(
                status_code=503,
                detail="Card generation is temporarily unavailable. Please try again in a few minutes.",
            )
        logger.warning("Generation %s failed: %s", generation_id, e.kind)
        raise HTTPException(status_code=502, detail=RETRY_MESSAGE)
    except CardGenerationSetupError as e:
        record_outcome(db, reservation, "setup_error")
        # Safe to log in full: the message is the service's own text
        logger.error("Generation %s failed: setup error: %s", generation_id, e)
        raise HTTPException(status_code=500, detail="Card generation isn't available right now.")
    except Exception as e:
        record_outcome(db, reservation, "internal_error")
        # The type and stack frames only, since the message could contain the notes
        logger.error(
            "Generation %s failed: unexpected %s\n%s",
            generation_id, type(e).__name__, "".join(traceback.format_tb(e.__traceback__)),
        )
        raise HTTPException(status_code=502, detail=RETRY_MESSAGE)

    record_outcome(db, reservation, result.output.status, result.metadata)
    remaining = remaining_generations(db, current_user)

    # Nothing is saved to the deck; the user reviews the cards first
    if result.output.status == "rejected":
        return GenerateRejected(status="rejected", reason=result.output.reason, remaining=remaining)
    cards = [
        GeneratedCard(question=card.question, answer=card.answer, source=card.source)
        for card in result.output.cards
    ]
    return GenerateSuccess(status="ok", cards=cards, remaining=remaining)


@router.get("/generations/remaining", response_model=GenerationRemaining)
def get_remaining_generations(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return GenerationRemaining(
        remaining=remaining_generations(db, current_user),
        limit=user_limit(current_user),
    )
