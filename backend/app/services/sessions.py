# backend/app/services/sessions.py
from typing import Dict, List
import time

# Simple in-memory session store for prototypes.
# For production switch to Redis or other persistent store.

SessionHistory = Dict[str, List[Dict]]

_sessions: SessionHistory = {}

MAX_HISTORY_ENTRIES = 12  # keep last N messages


def get_history(session_id: str) -> List[dict]:
    return _sessions.get(session_id, [])


def append_turn(session_id: str, role: str, text: str) -> None:
    if session_id not in _sessions:
        _sessions[session_id] = []
    _sessions[session_id].append({"role": role, "text": text, "ts": int(time.time())})
    # trim
    if len(_sessions[session_id]) > MAX_HISTORY_ENTRIES:
        _sessions[session_id] = _sessions[session_id][-MAX_HISTORY_ENTRIES:]


def clear_session(session_id: str) -> None:
    _sessions.pop(session_id, None)
