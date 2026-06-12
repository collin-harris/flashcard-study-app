from sqlalchemy import Column, ForeignKey, Integer, String
from app.database import Base

class Deck(Base):
    __tablename__ = 'decks'

    deck_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    name = Column(String, nullable=False)