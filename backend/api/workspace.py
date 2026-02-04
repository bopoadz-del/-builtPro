"""Workspace state API."""

from __future__ import annotations

from datetime import datetime
import uuid

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/workspace")


_DEFAULT_STATE = {
    "activeProjectId": "villa-100",
    "activeChatId": "villa-ops",
    "microphoneEnabled": False,
    "conversations": {
        "villa-ops": {
            "id": "villa-ops",
            "context": {"summary": "Operations chat"},
            "timeline": [
                {
                    "messages": [
                        {"id": "msg-1", "body": "Welcome", "timestamp": datetime.utcnow().isoformat()}
                    ]
                }
            ],
        }
    },
    "chatGroups": [
        {
            "id": "default",
            "title": "Active",
            "chats": [
                {"id": "villa-ops", "title": "Villa Ops", "preview": "Welcome"},
            ],
        }
    ],
}

_state = _DEFAULT_STATE.copy()


def _reset_state_for_tests() -> None:
    global _state
    _state = {
        "activeProjectId": _DEFAULT_STATE["activeProjectId"],
        "activeChatId": _DEFAULT_STATE["activeChatId"],
        "microphoneEnabled": False,
        "conversations": {**_DEFAULT_STATE["conversations"]},
        "chatGroups": [
            {
                "id": "default",
                "title": "Active",
                "chats": [
                    {"id": "villa-ops", "title": "Villa Ops", "preview": "Welcome"},
                ],
            }
        ],
    }


@router.get("/shell")
def get_shell():
    return {
        "activeProjectId": _state["activeProjectId"],
        "activeChatId": _state["activeChatId"],
        "microphoneEnabled": _state["microphoneEnabled"],
        "conversations": list(_state["conversations"].keys()),
        "chatGroups": _state["chatGroups"],
    }


@router.post("/chats")
def create_chat(payload: dict):
    project_id = payload.get("projectId")
    if not project_id:
        raise HTTPException(status_code=400, detail="projectId required")
    chat_id = f"draft-{uuid.uuid4().hex[:8]}"
    conversation = {
        "id": chat_id,
        "context": {"summary": f"Draft conversation for {project_id}"},
        "timeline": [],
    }
    _state["conversations"][chat_id] = conversation
    _state["chatGroups"][0]["chats"].append(
        {"id": chat_id, "title": f"Draft {project_id}", "preview": ""}
    )
    return {"conversation": conversation, "chatGroups": _state["chatGroups"]}


@router.post("/chats/{chat_id}/messages")
def submit_message(chat_id: str, payload: dict):
    conversation = _state["conversations"].get(chat_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    body = payload.get("body", "")
    message = {"id": f"msg-{uuid.uuid4().hex[:6]}", "body": body, "timestamp": datetime.utcnow().isoformat()}
    if not conversation["timeline"]:
        conversation["timeline"].append({"messages": []})
    conversation["timeline"][0]["messages"].append(message)

    for chat in _state["chatGroups"][0]["chats"]:
        if chat["id"] == chat_id:
            chat["preview"] = body[:100]
    return {"conversation": conversation, "chatGroups": _state["chatGroups"]}


@router.post("/microphone")
def toggle_microphone(payload: dict):
    enabled = bool(payload.get("enabled"))
    _state["microphoneEnabled"] = enabled
    return {"enabled": enabled}
