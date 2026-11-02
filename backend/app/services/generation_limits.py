import datetime
from typing import Literal, Optional

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app import config
from app.models.generation_request import GenerationRequest
from app.models.user import User
from app.services import card_generation

WINDOW = datetime.timedelta(hours=24)

# setup_error rows don't count toward any limit: they mean the deployment is
# misconfigured, and counting them would keep users locked out for a day
# after the fix. Every other row counts, pending ones included.
UNCOUNTED_STATUSES = ("setup_error",)

# Key for the Postgres advisory lock that serializes reservations. Any fixed
# number works; nothing else in the app takes advisory locks.
RESERVATION_LOCK_KEY = 4_042_001

LimitScope = Literal["user", "demo", "global"]


class GenerationLimitReached(Exception):
    def __init__(self, scope: LimitScope, limit: int):
        super().__init__(f"{scope} generation limit of {limit} reached")
        self.scope = scope
        self.limit = limit


def is_demo_account(user: User) -> bool:
    return user.email == config.DEMO_ACCOUNT_EMAIL


def user_limit(user: User) -> int:
    # The demo account's cap replaces the per-user one
    if is_demo_account(user):
        return config.GENERATION_LIMIT_DEMO
    return config.GENERATION_LIMIT_PER_USER


def _usage(db: Session, user: User) -> tuple[int, int]:
    # Returns the user's count and the global count over the window.
    # Both compare against the database's clock, the same one that sets
    # created_at.
    counted = db.query(func.count(GenerationRequest.generation_id)).filter(
        GenerationRequest.created_at > func.now() - WINDOW,
        GenerationRequest.status.notin_(UNCOUNTED_STATUSES),
    )
    user_count = counted.filter(GenerationRequest.user_id == user.user_id).scalar()
    global_count = counted.scalar()
    return user_count, global_count


def remaining_generations(db: Session, user: User) -> int:
    # Whichever cap is closer applies, so this is what the user can actually do
    user_count, global_count = _usage(db, user)
    return max(0, min(user_limit(user) - user_count, config.GENERATION_LIMIT_GLOBAL - global_count))


def reserve_generation(db: Session, user: User, input_chars: int) -> GenerationRequest:
    # The lock makes the count and the insert a single step, so two concurrent
    # requests can't both see room for one more. It's transaction-scoped, so
    # the commit or rollback below releases it.
    db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": RESERVATION_LOCK_KEY})

    user_count, global_count = _usage(db, user)
    # When both caps are reached, the user's own is the one reported
    if user_count >= user_limit(user):
        db.rollback()
        raise GenerationLimitReached("demo" if is_demo_account(user) else "user", user_limit(user))
    if global_count >= config.GENERATION_LIMIT_GLOBAL:
        db.rollback()
        raise GenerationLimitReached("global", config.GENERATION_LIMIT_GLOBAL)

    # Committed before the API call, so the row counts for concurrent
    # requests and no transaction stays open while waiting on the API
    reservation = GenerationRequest(
        user_id=user.user_id,
        model=card_generation.MODEL,
        prompt_version=card_generation.PROMPT_VERSION,
        prompt_hash=card_generation.get_prompt_hash(),
        status="pending",
        input_chars=input_chars,
    )
    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


def record_outcome(
    db: Session,
    reservation: GenerationRequest,
    status: str,
    metadata: Optional[card_generation.GenerationMetadata] = None,
):
    # Tokens, cost, and latency stay null when no response came back
    reservation.status = status
    if metadata is not None:
        reservation.input_tokens = metadata.input_tokens
        reservation.output_tokens = metadata.output_tokens
        reservation.cost_usd = metadata.cost_usd
        reservation.latency_seconds = metadata.latency_seconds

    db.commit()
