import json
from collections.abc import Iterator
from typing import Any
from uuid import uuid4

from django.conf import settings

from .base import AIProvider, ChatResult, ToolCall


def _parse_arguments(raw: Any) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


class MistralProvider(AIProvider):
    name = "mistral"

    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.MISTRAL_API_KEY
        self.model = model or settings.MISTRAL_MODEL
        self._client = None

    def _client_or_raise(self):
        if not self.api_key:
            raise RuntimeError("MISTRAL_API_KEY is not configured.")
        if self._client is None:
            from mistralai import Mistral

            self._client = Mistral(api_key=self.api_key)
        return self._client

    def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.4,
    ) -> ChatResult:
        client = self._client_or_raise()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        response = client.chat.complete(**kwargs)
        choice = response.choices[0]
        message = choice.message
        tool_calls: list[ToolCall] = []
        raw_calls = getattr(message, "tool_calls", None) or []
        for call in raw_calls:
            function = getattr(call, "function", None)
            name = getattr(function, "name", "") if function else ""
            arguments = _parse_arguments(getattr(function, "arguments", "{}") if function else "{}")
            tool_calls.append(
                ToolCall(
                    id=getattr(call, "id", None) or f"call_{uuid4().hex[:12]}",
                    name=name,
                    arguments=arguments,
                )
            )
        content = message.content or ""
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else getattr(part, "text", str(part))
                for part in content
            )
        return ChatResult(content=content or "", tool_calls=tool_calls, raw=message)

    def stream(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.4,
    ) -> Iterator[str]:
        client = self._client_or_raise()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        stream = client.chat.stream(**kwargs)
        for event in stream:
            data = getattr(event, "data", None)
            if not data or not getattr(data, "choices", None):
                continue
            delta = data.choices[0].delta
            piece = getattr(delta, "content", None)
            if piece:
                if isinstance(piece, list):
                    text = "".join(
                        p.get("text", "") if isinstance(p, dict) else getattr(p, "text", "")
                        for p in piece
                    )
                    if text:
                        yield text
                elif isinstance(piece, str):
                    yield piece
