import hashlib
import os
import time
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional, Union

import anthropic
from pydantic import BaseModel, Field, TypeAdapter, ValidationError


# Every evaluation run records these settings, so changing any of them means
# the results are no longer comparable with earlier runs.
MODEL = "claude-haiku-4-5-20251001"
PROMPT_VERSION = "v1"
MAX_TOKENS = 4096
REQUEST_TIMEOUT_SECONDS = 60

# SDK 1.x removed temperature as a keyword argument, so it's sent through
# extra_body instead. Haiku 4.5 accepts it, but Opus 4.7 and later models
# reject any temperature with a 400 -- remove it if the model changes to one.
TEMPERATURE = 0

# Haiku 4.5 base rates in USD per million tokens, from
# https://platform.claude.com/docs/en/about-claude/pricing (checked 2026-09-29).
# Prompt caching isn't used, so cache read/write rates don't apply.
INPUT_COST_PER_MTOK = 1.00
OUTPUT_COST_PER_MTOK = 5.00

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# The notes are joined with concatenation, never str.format, because notes
# can contain literal braces (code samples, for example).
USER_MESSAGE_PREFIX = "<notes>\n"
USER_MESSAGE_SUFFIX = "\n</notes>"


class Card(BaseModel):
    question: str
    answer: str
    source: list[str] = Field(min_length=1)


# Pydantic describes a single-value Literal with `const`, which the SDK moves
# into description text before sending, so the API wouldn't enforce it.
# Adding `enum` gets the allowed value sent as a real constraint.
class GeneratedCards(BaseModel):
    status: Literal["ok"] = Field(json_schema_extra={"enum": ["ok"]})
    cards: list[Card] = Field(min_length=1)


class Rejection(BaseModel):
    status: Literal["rejected"] = Field(json_schema_extra={"enum": ["rejected"]})
    reason: str


GenerationOutput = Union[GeneratedCards, Rejection]

_output_adapter = TypeAdapter(GenerationOutput)
OUTPUT_SCHEMA = anthropic.transform_schema(_output_adapter.json_schema())


class GenerationMetadata(BaseModel):
    model: str
    prompt_version: str
    prompt_hash: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_seconds: float


class GenerationResult(BaseModel):
    output: GenerationOutput
    metadata: GenerationMetadata
    raw_text: str


ErrorKind = Literal["api_error", "truncated", "refusal", "invalid_output"]


class CardGenerationError(Exception):
    # raw_text and metadata are set whenever a response actually came back,
    # so a failed call's output and cost can still be recorded.
    def __init__(
        self,
        kind: ErrorKind,
        message: str,
        raw_text: Optional[str] = None,
        metadata: Optional[GenerationMetadata] = None,
    ):
        super().__init__(message)
        self.kind = kind
        self.raw_text = raw_text
        self.metadata = metadata


@lru_cache(maxsize=1)
def _load_system_prompt() -> str:
    # Loaded on first use, not at import, so importing this module never
    # touches the filesystem.
    path = PROMPTS_DIR / f"card_generation_{PROMPT_VERSION}.txt"
    return path.read_text(encoding="utf-8")


def get_prompt_hash() -> str:
    # Covers everything sent besides the notes themselves, so an edit to the
    # prompt without a version bump still shows up as a different hash.
    combined = _load_system_prompt() + USER_MESSAGE_PREFIX + USER_MESSAGE_SUFFIX
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:12]


def _estimate_cost(input_tokens: int, output_tokens: int) -> float:
    return (input_tokens * INPUT_COST_PER_MTOK + output_tokens * OUTPUT_COST_PER_MTOK) / 1_000_000


def generate_cards(notes: str) -> GenerationResult:
    # Checked here rather than at import so the app and test suite can run
    # without the key.
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Card generation needs it to call the Anthropic API."
        )

    client = anthropic.Anthropic(api_key=api_key, timeout=REQUEST_TIMEOUT_SECONDS)

    # Latency covers the whole call, including any automatic SDK retries.
    start = time.perf_counter()
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=_load_system_prompt(),
            messages=[
                {"role": "user", "content": USER_MESSAGE_PREFIX + notes + USER_MESSAGE_SUFFIX}
            ],
            output_config={"format": {"type": "json_schema", "schema": OUTPUT_SCHEMA}},
            extra_body={"temperature": TEMPERATURE},
        )
    except anthropic.APITimeoutError as e:
        raise CardGenerationError("api_error", f"Request timed out: {e}") from e
    except anthropic.APIConnectionError as e:
        raise CardGenerationError("api_error", f"Could not reach the Anthropic API: {e}") from e
    except anthropic.RateLimitError as e:
        raise CardGenerationError("api_error", f"Rate limited by the Anthropic API: {e}") from e
    except anthropic.APIStatusError as e:
        raise CardGenerationError("api_error", f"Anthropic API returned {e.status_code}: {e}") from e
    latency = time.perf_counter() - start

    metadata = GenerationMetadata(
        model=response.model,
        prompt_version=PROMPT_VERSION,
        prompt_hash=get_prompt_hash(),
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        cost_usd=_estimate_cost(response.usage.input_tokens, response.usage.output_tokens),
        latency_seconds=latency,
    )
    raw_text = "".join(block.text for block in response.content if block.type == "text")

    # Structured outputs only guarantee valid JSON when generation finishes
    # normally, so these are checked before parsing.
    if response.stop_reason == "max_tokens":
        raise CardGenerationError(
            "truncated", f"Output hit the {MAX_TOKENS}-token limit before finishing.", raw_text, metadata
        )
    if response.stop_reason == "refusal":
        raise CardGenerationError("refusal", "The model declined to respond.", raw_text, metadata)

    try:
        output = _output_adapter.validate_json(raw_text)
    except ValidationError as e:
        raise CardGenerationError(
            "invalid_output", f"Output did not match the expected structure: {e}", raw_text, metadata
        ) from e

    return GenerationResult(output=output, metadata=metadata, raw_text=raw_text)
