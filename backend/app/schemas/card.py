from pydantic import BaseModel, ConfigDict, Field


class CardCreate(BaseModel):
    # Stripped before the length check, so an empty or whitespace-only side
    # is rejected
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)


class CardUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str | None = Field(default=None, min_length=1)
    answer: str | None = Field(default=None, min_length=1)


class CardBulkCreate(BaseModel):
    cards: list[CardCreate] = Field(min_length=1, max_length=100)


class CardResponse(BaseModel):
    card_id: int
    deck_id: int
    question: str
    answer: str

    model_config = ConfigDict(from_attributes=True)
