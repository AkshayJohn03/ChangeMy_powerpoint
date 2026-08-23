"""Persistent feedback capture for human-in-the-loop review."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

FEEDBACK_DIR = Path(os.environ.get("BRANDMORPH_FEEDBACK_DIR", "data/feedback"))


def save_feedback(session_id: str, decisions: list[dict]):
    FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
    session_dir = FEEDBACK_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "feedback_v1",
        "session_id": session_id,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "decisions": [],
    }
    for d in decisions:
        payload["decisions"].append({
            "node_id": d.get("node_id", ""),
            "model_action": d.get("action", ""),
            "confidence": d.get("confidence", 0),
            "policy": d.get("policy", ""),
            "user_decision": d.get("user_decision"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    out = session_dir / "feedback.json"
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    return str(out)


def load_feedback_session(session_id: str) -> dict:
    path = FEEDBACK_DIR / session_id / "feedback.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
