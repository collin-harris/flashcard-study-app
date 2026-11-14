from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, func
from app.database import Base


class GenerationRequest(Base):
    __tablename__ = 'generation_requests'
    __table_args__ = (
        # Per-user counts filter on user_id then created_at; global counts
        # filter on created_at alone.
        Index("ix_generation_requests_user_id_created_at", "user_id", "created_at"),
        Index("ix_generation_requests_created_at", "created_at"),
    )

    generation_id = Column(Integer, primary_key=True)
    # SET NULL rather than CASCADE: a row holds no content, only usage and
    # cost, so it's kept after its user is deleted. That keeps the global
    # cap and the spend history accurate.
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    model = Column(String, nullable=False)
    prompt_version = Column(String, nullable=False)
    prompt_hash = Column(String, nullable=False)
    # pending, ok, rejected, an ErrorKind from card_generation, setup_error,
    # or internal_error
    status = Column(String, nullable=False)
    input_chars = Column(Integer, nullable=False)
    # Null when no response came back to measure
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    cost_usd = Column(Numeric(10, 6))
    latency_seconds = Column(Float)
