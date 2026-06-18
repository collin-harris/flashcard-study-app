from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.models.card_review import CardReview
from app.models.deck import Deck
from app.models.flashcard import Flashcard
from app.routers.auth import get_db, get_current_user
from app.schemas.review import ReviewRequest, ReviewResponse, DueCardResponse
from app.services.sm2 import calculate_sm2

router = APIRouter()


@router.get("/decks/{deck_id}/study", response_model=list[DueCardResponse])
def get_due_cards(
    deck_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Get every card in this deck
    cards = db.query(Flashcard).filter(Flashcard.deck_id == deck_id).all()

    # Get this user's existing review state for those cards, if any
    card_ids = [card.card_id for card in cards]
    card_reviews = db.query(CardReview).filter(
        CardReview.user_id == current_user.user_id,
        CardReview.card_id.in_(card_ids)
    ).all()

    # Map card_id -> review for O(1) lookup in the loop below
    review_dict = {}
    for review in card_reviews:
        review_dict[review.card_id] = review

    # Keep only the cards that are due now, or have never been studied
    due_cards = []
    for card in cards:
        review = review_dict.get(card.card_id)
        if review is None:
            # Never studied - due today
            next_review_date = date.today()
        elif review.next_review_date <= date.today():
            # Due now
            next_review_date = review.next_review_date
        else:
            continue  # Not due yet, skip this card

        due_cards.append(DueCardResponse(
            card_id=card.card_id,
            question=card.question,
            answer=card.answer,
            next_review_date=next_review_date
        ))

    return due_cards


@router.post("/decks/{deck_id}/cards/{card_id}/review", response_model=ReviewResponse)
def submit_review(
    deck_id: int,
    card_id: int,
    review_data: ReviewRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Confirm the deck exists and belongs to the current user
    deck = db.query(Deck).filter(Deck.deck_id == deck_id).first()
    if deck is None:
        raise HTTPException(status_code=404, detail="Deck not found")
    if deck.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Confirm the card exists in this deck
    card = db.query(Flashcard).filter(
        Flashcard.card_id == card_id,
        Flashcard.deck_id == deck_id
    ).first()
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    
    # Look up this user's existing review state for this card, if any
    card_review = db.query(CardReview).filter(
        CardReview.user_id == current_user.user_id,
        CardReview.card_id == card_id
    ).first()

    # Use SM-2 defaults on a first-ever review, otherwise the stored state
    if card_review is None:
        easiness, repetitions, interval = 2.5, 0, 0
    else:
        easiness, repetitions, interval = card_review.easiness, card_review.repetitions, card_review.interval

    # Apply the SM-2 algorithm to get the new state
    new_easiness, new_repetitions, new_interval, next_review_date = calculate_sm2(
        easiness, repetitions, interval, review_data.rating
    )

    # Create a new review record on first review, otherwise update the existing one
    if card_review is None:
        card_review = CardReview(
            user_id=current_user.user_id,
            card_id=card_id,
            easiness=new_easiness,
            repetitions=new_repetitions,
            interval=new_interval,
            next_review_date=next_review_date
        )
        db.add(card_review)
    else:
        card_review.easiness = new_easiness
        card_review.repetitions = new_repetitions
        card_review.interval = new_interval
        card_review.next_review_date = next_review_date

    db.commit()
    db.refresh(card_review)

    return card_review