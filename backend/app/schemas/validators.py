from pydantic import AfterValidator
from pydantic_core import PydanticCustomError


def required_text(message: str) -> AfterValidator:
    # Strips surrounding whitespace, then rejects what's left if it's empty.
    # The message is a full sentence, which the frontend shows as it is.
    def check(value: str) -> str:
        value = value.strip()
        if not value:
            raise PydanticCustomError("empty_text", message)
        return value

    return AfterValidator(check)
