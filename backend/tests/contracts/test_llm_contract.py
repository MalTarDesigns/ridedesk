from typing import Any

import pytest
from pydantic import BaseModel

from ridedesk.adapters.llm import LlmClient, LlmError, MockLlm


class Pickup(BaseModel):
    pickup: str
    passengers: int


def arrange(llm: LlmClient, response: dict[str, Any]) -> None:
    """Give the mock its scripted answer. A real client answers the prompt itself."""
    if isinstance(llm, MockLlm):
        llm.queue(response)


def test_a_reply_is_parsed_into_the_schema_with_usage(llm: LlmClient) -> None:
    arrange(llm, {"pickup": "JFK", "passengers": 4})

    result = llm.complete_json(
        "Extract the pickup and passenger count as JSON.",
        "Pick up 4 of us at JFK.",
        Pickup,
    )

    assert isinstance(result.parsed, Pickup)
    assert result.model
    assert result.input_tokens >= 0
    assert result.output_tokens >= 0
    assert result.latency_ms >= 0


def test_a_reply_that_does_not_fit_the_schema_raises_llm_error(llm: LlmClient) -> None:
    if not isinstance(llm, MockLlm):
        pytest.skip("only a scripted client can be made to answer off-schema")
    arrange(llm, {"pickup": "JFK", "passengers": "lots"})

    with pytest.raises(LlmError):
        llm.complete_json("Extract as JSON.", "Pick up lots of us at JFK.", Pickup)
