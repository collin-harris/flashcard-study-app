from sqlalchemy import Column, Date, Float, ForeignKey, Integer
from app.database import Base


class CardReview(Base):
    __tablename__ = 'card_reviews'

    user_id = Column(Integer, ForeignKey("users.user_id"), primary_key=True)
    card_id = Column(Integer, ForeignKey("flashcards.card_id"), primary_key=True)
    easiness = Column(Float, nullable=False)
    repetitions = Column(Integer, nullable=False)
    interval = Column(Integer, nullable=False)
    next_review_date = Column(Date, nullable=False)
