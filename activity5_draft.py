from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, MutableMapping
from typing import Any


DRAFT_VERSION = 1
DRAFT_STATE_KEYS = (
    "a5v4_identity",
    "a5v4_productivity",
    "a5v4_wellbeing",
    "a5v4_collaboration",
    "a5v4_budget",
    "a5v4_risk",
    "a5v4_horizon",
    "a5v4_operational",
    "a5v4_diagnostic_focus",
    "a5v4_diagnostic_evidence",
    "a5v4_diagnostic_uncertainty",
    "a5v4_before",
    "a5v4_scenario",
    "a5v4_after",
    "a5v4_chosen",
    "a5v4_final_evidence",
    "a5v4_final_contrary",
    "a5v4_final_tradeoff",
    "a5v4_final_change",
    "a5v4_final_condition",
    "a5v4_sheet",
)


def browser_draft_key(email: str) -> str:
    """Return a non-identifying browser key scoped to the signed-in student."""
    digest = hashlib.sha256(email.strip().casefold().encode("utf-8")).hexdigest()[:20]
    return f"udd_activity_05_draft_{digest}"


def encode_draft(state: Mapping[str, Any]) -> str:
    payload = {
        "version": DRAFT_VERSION,
        "state": {key: state[key] for key in DRAFT_STATE_KEYS if key in state},
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def decode_draft(raw: Any) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        payload = json.loads(raw) if isinstance(raw, str) else raw
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict) or payload.get("version") != DRAFT_VERSION:
        return None
    state = payload.get("state")
    if not isinstance(state, dict):
        return None
    return {key: state[key] for key in DRAFT_STATE_KEYS if key in state}


def restore_draft(target: MutableMapping[str, Any], draft: Mapping[str, Any]) -> int:
    restored = 0
    for key in DRAFT_STATE_KEYS:
        if key in draft and key not in target:
            target[key] = draft[key]
            restored += 1
    return restored


def clear_activity_state(target: MutableMapping[str, Any]) -> None:
    for key in list(target):
        text_key = str(key)
        component_state = text_key.startswith(("a5v4_browser_storage_", "a5v4_save_", "a5v4_delete_draft"))
        if text_key.startswith("a5v4_") and not component_state:
            target.pop(key, None)
