from datetime import date
from pydantic import BaseModel, ConfigDict, Field


class ReviewRequest(BaseModel):
    rating: int = Field(ge=0, le=5)


class ReviewResponse(BaseModel):
    card_id: int
    easiness: float
    repetitions: int
    interval: int
    next_review_date: date

    model_config = ConfigDict(from_attributes=True)


class DueCardResponse(BaseModel):
    card_id: int
    question: str
    answer: str
    next_review_date: date

    model_config = ConfigDict(from_attributes=True)
    