"""Pipeline 3 output node — store report, complete session, stop the sandbox."""

from __future__ import annotations

from typing import Any

from ..common.butterbase import Butterbase
from ..nodes import daytona_node


def publish(
    *,
    bb: Butterbase,
    child_id: str,
    session_id: str,
    report_json: dict[str, Any],
    sandbox_id: str | None,
) -> dict[str, Any]:
    report_row = bb.insert(
        "reports",
        {
            "child_id": child_id,
            "session_id": session_id,
            "report_json": report_json,
            "summary_text": report_json.get("parent_summary", ""),
        },
    )

    bb.update("sessions", session_id, {"status": "complete"})

    # Realtime push — Contract C session_end.
    bb.publish(
        f"child:{child_id}:session",
        {"event": "session_end", "session_id": session_id, "report_id": report_row["id"]},
    )

    # Stop the sandbox to preserve state without burning compute (plan §5).
    if sandbox_id:
        daytona_node.stop(sandbox_id)

    return {"report_id": report_row["id"]}
