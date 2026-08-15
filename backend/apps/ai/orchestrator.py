import json
from collections.abc import Iterator

from apps.conversations.models import Conversation, Message
from apps.conversations.views import get_or_create_today

from .context import build_user_context
from .prompts import ONBOARDING_OPENER, STARTUP_INSTRUCTION, system_prompt
from .providers import get_provider
from .tools.definitions import TOOLS
from .tools.executor import executor


def _history(conversation: Conversation, limit: int = 24) -> list[dict]:
    messages = []
    for msg in conversation.messages.order_by("created_at")[max(0, conversation.messages.count() - limit) :]:
        if msg.role in {"user", "assistant"} and msg.content:
            messages.append({"role": msg.role, "content": msg.content})
    return messages


def _tool_message(call_id: str, name: str, result: dict) -> dict:
    return {
        "role": "tool",
        "name": name,
        "tool_call_id": call_id,
        "content": json.dumps(result, default=str),
    }


def _assistant_tool_message(result) -> dict:
    raw = result.raw
    if raw is not None:
        try:
            if hasattr(raw, "model_dump"):
                dumped = raw.model_dump()
                dumped.setdefault("role", "assistant")
                return dumped
        except Exception:
            pass
    tool_calls = []
    for call in result.tool_calls:
        tool_calls.append(
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments),
                },
            }
        )
    return {
        "role": "assistant",
        "content": result.content or None,
        "tool_calls": tool_calls,
    }


class Orchestrator:
    def __init__(self):
        self.provider = get_provider()

    def _run_tools(self, user, result, messages: list, ui_blocks: list) -> list[str]:
        events = []
        messages.append(_assistant_tool_message(result))
        for call in result.tool_calls:
            events.append(call.name)
            payload = executor.execute(user, call.name, call.arguments)
            if payload.get("ui"):
                ui_blocks.append(payload["ui"])
            messages.append(_tool_message(call.id, call.name, payload))
        return events

    def stream_reply(self, user, conversation: Conversation, user_text: str) -> Iterator[dict]:
        user_msg = Message.objects.create(conversation=conversation, role="user", content=user_text)
        yield {"event": "user_message", "data": {"id": user_msg.id}}

        context = build_user_context(user)
        kind = conversation.kind
        messages: list[dict] = [
            {"role": "system", "content": system_prompt(context, kind=kind)},
            *_history(conversation),
        ]

        ui_blocks: list[dict] = []
        tools_used: list[str] = []
        max_iters = 6
        final_text = ""

        try:
            for _ in range(max_iters):
                result = self.provider.complete(messages, tools=TOOLS)
                if result.tool_calls:
                    used = self._run_tools(user, result, messages, ui_blocks)
                    tools_used.extend(used)
                    yield {"event": "tools", "data": {"names": used}}
                    continue
                break
            else:
                result = self.provider.complete(
                    messages + [{"role": "user", "content": "Stop calling tools. Reply to the user now."}],
                    tools=None,
                )

            if result.content:
                final_text = result.content
                yield {"event": "token", "data": {"content": result.content}}
            else:
                for chunk in self.provider.stream(messages, tools=None):
                    final_text += chunk
                    yield {"event": "token", "data": {"content": chunk}}
        except Exception as exc:
            if not final_text:
                final_text = (
                    "I couldn't reach the model just now. "
                    "Add your MISTRAL_API_KEY to `.env` and restart the backend, then try again."
                )
            yield {"event": "token", "data": {"content": final_text}}
            yield {"event": "error", "data": {"message": str(exc)}}

        assistant = Message.objects.create(
            conversation=conversation,
            role="assistant",
            content=final_text,
            metadata={"blocks": ui_blocks, "tools": tools_used},
        )
        conversation.save(update_fields=["updated_at"])
        yield {
            "event": "done",
            "data": {
                "message_id": assistant.id,
                "blocks": ui_blocks,
                "tools": tools_used,
                "schedule_changed": any(
                    t in tools_used
                    for t in {
                        "create_schedule_item",
                        "update_schedule_item",
                        "delete_schedule_item",
                        "move_schedule_item",
                        "complete_task",
                    }
                ),
                "goals_changed": any(t in tools_used for t in {"create_goal", "update_goal", "update_preferences"}),
            },
        }

    def ensure_opener(self, user) -> Conversation:
        profile = getattr(user, "profile", None)
        kind = "onboarding" if profile and not profile.onboarding_completed else "daily"
        convo = get_or_create_today(user, kind=kind)
        if convo.messages.exists():
            return convo

        if kind == "onboarding":
            Message.objects.create(conversation=convo, role="assistant", content=ONBOARDING_OPENER)
            return convo

        context = build_user_context(user)
        messages = [
            {"role": "system", "content": system_prompt(context, kind="daily")},
            {"role": "user", "content": STARTUP_INSTRUCTION},
        ]
        try:
            result = self.provider.complete(messages, tools=None, temperature=0.5)
            text = (result.content or "").strip() or "What's the plan for the next few hours?"
        except Exception:
            rec = context.get("recommendation") or {}
            top = rec.get("top_recommendation")
            if top:
                text = (
                    f"You have about {rec.get('available_minutes', 0)} minutes free. "
                    f"{top['reason']} I'd start with {top['title']} for {top['suggested_minutes']} minutes. "
                    "How do you want to use the next block?"
                )
            else:
                text = "What's the plan for the next few hours?"
        Message.objects.create(conversation=convo, role="assistant", content=text)
        return convo


orchestrator = Orchestrator()
