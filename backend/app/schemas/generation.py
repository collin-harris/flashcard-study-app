from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field


class GenerateRequest(BaseModel):
    # Stripped before the length check, so whitespace-only notes are a 422
    # rather than a request that uses up the user's quota
    model_config = ConfigDict(str_strip_whitespace=True)

    notes: str = Field(min_length=1, max_length=2000)


# The API's own card shape, kept separate from card_generation.Card so the
# model's output schema can change without changing the API contract
class GeneratedCard(BaseModel):
    question: str
    answer: str
    source: list[str]


class GenerateSuccess(BaseModel):
    status: Literal["ok"]
    cards: list[GeneratedCard]
    remaining: int


class GenerateRejected(BaseModel):
    status: Literal["rejected"]
    reason: str
    remaining: int


GenerateResponse = Annotated[Union[GenerateSuccess, GenerateRejected], Field(discriminator="status")]


class GenerationRemaining(BaseModel):
    remaining: int
    limit: int
