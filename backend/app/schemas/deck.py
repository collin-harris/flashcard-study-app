from pydantic import BaseModel, ConfigDict


class DeckCreate(BaseModel):
    name: str


class DeckUpdate(BaseModel):
    name: str | None = None


class DeckResponse(BaseModel):
    deck_id: int
    user_id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class DeckWithCardCount(DeckResponse):
    card_count: int
