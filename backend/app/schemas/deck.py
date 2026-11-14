from typing import Annotated
from pydantic import BaseModel, ConfigDict

from app.schemas.validators import required_text

# Stripped, and rejected if nothing is left
DeckName = Annotated[str, required_text("Deck name can't be empty.")]


class DeckCreate(BaseModel):
    name: DeckName


class DeckUpdate(BaseModel):
    name: DeckName | None = None


class DeckResponse(BaseModel):
    deck_id: int
    user_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DeckWithCardCount(DeckResponse):
    card_count: int
