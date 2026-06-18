from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base


class Flashcard(Base):
    __tablename__ = 'flashcards'

    card_id = Column(Integer, primary_key=True)
    deck_id = Column(Integer, ForeignKey("decks.deck_id", ondelete="CASCADE"), nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
