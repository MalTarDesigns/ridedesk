from collections import deque
from typing import Any, Protocol

from pydantic import BaseModel, ValidationError


class LlmError(RuntimeError):
    """The model call failed or returned something that does not fit the schema."""


class LlmResult[T: BaseModel](BaseModel):
    parsed: T
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


class LlmClient(Protocol):
    def complete_json[T: BaseModel](self, system: str, user: str, schema: type[T]) -> LlmResult[T]:
        """Ask for JSON matching schema. Raises LlmError when it does not fit."""
        ...


class MockLlm:
    """Replays responses queued by a test, in order, and validates them like a real call."""

    def __init__(self) -> None:
        self.responses: deque[dict[str, Any]] = deque()
        self.calls: list[tuple[str, str]] = []

    def queue(self, response: dict[str, Any]) -> None:
        self.responses.append(response)

    def complete_json[T: BaseModel](self, system: str, user: str, schema: type[T]) -> LlmResult[T]:
        self.calls.append((system, user))
        if not self.responses:
            raise LlmError("no mock response queued")
        try:
            parsed = schema.model_validate(self.responses.popleft())
        except ValidationError as error:
            raise LlmError(f"response does not match {schema.__name__}") from error
        return LlmResult[T](
            parsed=parsed,
            model="mock",
            input_tokens=len(user.split()),
            output_tokens=0,
            latency_ms=0,
        )
