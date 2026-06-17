from pydantic import BaseModel, ConfigDict


class CardCreate(BaseModel):
    question: str
    answer: str


class CardUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None


class CardResponse(BaseModel):
    card_id: int
    deck_id: int
    question: str
    answer: str

    model_config = ConfigDict(from_attributes=True)
