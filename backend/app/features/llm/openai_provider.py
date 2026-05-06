from __future__ import annotations

import json
from typing import Any

from openai import OpenAI
from openai import OpenAIError
from pydantic import ValidationError

from app.features.llm.mock import MockLLMProvider
from app.features.llm.prompts import (
    CONTEXT_EXTRACTION_SYSTEM_PROMPT,
    RESPONSE_GENERATION_SYSTEM_PROMPT,
    context_extraction_user_prompt,
    response_generation_user_prompt,
)
from app.features.llm.schemas import (
    ContextExtractionInput,
    ContextExtractionResult,
    ResponseGenerationInput,
    ResponseGenerationResult,
)


class OpenAILLMProvider:
    provider_name = "openai"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        base_url: str,
        timeout_seconds: float = 20.0,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self.client = client or OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout_seconds,
        )
        self._fallback = MockLLMProvider(provider_name="mock_fallback")

    def extract_context(self, payload: ContextExtractionInput) -> ContextExtractionResult:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": CONTEXT_EXTRACTION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": context_extraction_user_prompt(
                            payload.existing_context_state,
                            payload.content,
                        ),
                    },
                ],
            )
            content = response.choices[0].message.content
            decoded = json.loads(content or "{}")
            if not isinstance(decoded, dict):
                return self._fallback.extract_context(payload)
            return self._result_from_decoded(payload, decoded)
        except (AttributeError, KeyError, IndexError, TypeError, json.JSONDecodeError):
            return self._fallback.extract_context(payload)
        except (OpenAIError, ValidationError):
            return self._fallback.extract_context(payload)

    def generate_response(self, payload: ResponseGenerationInput) -> ResponseGenerationResult:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.6,
                messages=[
                    {"role": "system", "content": RESPONSE_GENERATION_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": response_generation_user_prompt(payload.model_dump()),
                    },
                ],
            )
            content = (response.choices[0].message.content or "").strip()
            if not content:
                return self._fallback.generate_response(payload)
            return ResponseGenerationResult(provider=self.provider_name, content=content)
        except (AttributeError, KeyError, IndexError, TypeError):
            return self._fallback.generate_response(payload)
        except OpenAIError:
            return self._fallback.generate_response(payload)

    def _result_from_decoded(
        self,
        payload: ContextExtractionInput,
        decoded: dict[str, Any],
    ) -> ContextExtractionResult:
        merged_state = dict(payload.existing_context_state or {})
        model_state = decoded.get("context_state")
        if isinstance(model_state, dict):
            merged_state.update(model_state)
        return ContextExtractionResult(
            provider=self.provider_name,
            context_state=merged_state,
            context_summary=str(decoded.get("context_summary") or payload.content[:80]),
            confidence=_bounded_confidence(decoded.get("confidence", 0.5)),
        )


def _bounded_confidence(raw_value: Any) -> float:
    try:
        value = float(raw_value)
    except (TypeError, ValueError):
        return 0.5
    return max(0.0, min(value, 1.0))
