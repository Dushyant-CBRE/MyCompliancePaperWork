"""
LLM client using Anthropic Claude via Azure AI Foundry.

Wraps AnthropicFoundry to expose the same interface the agents use:
    client.chat.completions.create(model, messages, tools, tool_choice, temperature)

Anthropic differences handled here transparently:
  - system message extracted from messages list and passed separately
  - tool schemas converted from OpenAI function-calling format → Anthropic tool format
  - tool_choice mapped (auto → auto, required → any)
  - response wrapped in the same SimpleNamespace shape agents already consume
  - tool_calls on responses converted to the same SimpleNamespace shape
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache
from types import SimpleNamespace

import httpx

from backend.config import get_settings

logger = logging.getLogger(__name__)


def _openai_tools_to_anthropic(tools: list[dict]) -> list[dict]:
    """Convert OpenAI function-calling schema → Anthropic tools format."""
    result = []
    for t in tools:
        fn = t.get("function", {})
        result.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
        })
    return result


def _map_tool_choice(tool_choice) -> dict:
    if tool_choice == "required" or tool_choice == "any":
        return {"type": "any"}
    if isinstance(tool_choice, dict) and "function" in tool_choice:
        return {"type": "tool", "name": tool_choice["function"]["name"]}
    return {"type": "auto"}


def _wrap_response(response) -> SimpleNamespace:
    """
    Wrap an Anthropic Message into the OpenAI-compatible SimpleNamespace
    that all agents expect:
      result.choices[0].message.content    → str | None
      result.choices[0].message.tool_calls → list[SimpleNamespace] | None
      result.choices[0].finish_reason      → str
    """
    text_content = ""
    tool_calls = []

    for block in response.content:
        if block.type == "text":
            text_content += block.text
        elif block.type == "tool_use":
            tool_calls.append(
                SimpleNamespace(
                    id=block.id,
                    type="function",
                    function=SimpleNamespace(
                        name=block.name,
                        arguments=json.dumps(block.input),
                    ),
                )
            )

    finish_reason = "stop" if response.stop_reason == "end_turn" else response.stop_reason
    message = SimpleNamespace(
        content=text_content or None,
        role="assistant",
        tool_calls=tool_calls if tool_calls else None,
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message, finish_reason=finish_reason)],
        model=response.model,
    )


class _ChatCompletions:
    """Anthropic-backed chat.completions.create() compatible with the OpenAI SDK interface."""

    def __init__(self, client) -> None:
        self._client = client

    def create(self, model: str, messages: list[dict], **kwargs) -> SimpleNamespace:
        # ── Split system message out (Anthropic takes it separately) ────────
        system = ""
        filtered: list[dict] = []
        for m in messages:
            if m["role"] == "system":
                system += m["content"]
            else:
                filtered.append(m)

        # ── Convert messages to Anthropic format ───────────────────────────
        anthropic_msgs: list[dict] = []
        for m in filtered:
            role = m["role"]

            if role == "assistant":
                blocks = []
                if m.get("content"):
                    blocks.append({"type": "text", "text": m["content"]})
                for tc in (m.get("tool_calls") or []):
                    try:
                        inp = json.loads(tc["function"]["arguments"] or "{}")
                    except (json.JSONDecodeError, KeyError):
                        inp = {}
                    blocks.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": inp,
                    })
                if blocks:
                    anthropic_msgs.append({"role": "assistant", "content": blocks})

            elif role == "tool":
                # OpenAI tool result → Anthropic tool_result block in a user turn
                anthropic_msgs.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": m.get("tool_call_id", ""),
                        "content": str(m.get("content", "")),
                    }],
                })

            else:
                anthropic_msgs.append({"role": role, "content": m["content"]})

        # ── Build call kwargs ─────────────────────────────────────────────
        call_kwargs: dict = {
            "model": model,
            "max_tokens": kwargs.get("max_completion_tokens", 4096),
            "messages": anthropic_msgs,
        }
        if system:
            call_kwargs["system"] = system

        tools_raw = kwargs.get("tools")
        if tools_raw:
            call_kwargs["tools"] = _openai_tools_to_anthropic(tools_raw)
            call_kwargs["tool_choice"] = _map_tool_choice(kwargs.get("tool_choice", "auto"))

        temp = kwargs.get("temperature", 1.0)
        call_kwargs["temperature"] = max(0.0, min(1.0, float(temp)))

        response = self._client.messages.create(**call_kwargs)
        return _wrap_response(response)


class _ChatResource:
    def __init__(self, completions: _ChatCompletions) -> None:
        self.completions = completions


class AnthropicFoundryClient:
    """Drop-in replacement for the old CBREProxyClient, backed by AnthropicFoundry."""

    def __init__(self) -> None:
        settings = get_settings()
        try:
            from anthropic import AnthropicFoundry  # type: ignore
        except ImportError as exc:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            ) from exc

        raw_client = AnthropicFoundry(
            api_key=settings.anthropic_api_key,
            base_url=settings.anthropic_endpoint,
            http_client=httpx.Client(verify=False),
        )
        self.chat = _ChatResource(_ChatCompletions(raw_client))


@lru_cache(maxsize=1)
def get_llm_client() -> AnthropicFoundryClient:
    return AnthropicFoundryClient()
