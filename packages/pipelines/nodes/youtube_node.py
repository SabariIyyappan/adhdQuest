"""YouTube lookup node (Pipeline 2, step 3).

Delegates to the Butterbase `youtube-lookup` serverless function so the API key and
quota handling stay on the backend. Returns the video recommendation, or None when
the remaining attention window is too small to show a video (plan §6 Feature 2).
"""

from __future__ import annotations

from typing import Any

from ..common.butterbase import Butterbase

_bb = Butterbase()


def run(concept_tag: str, remaining_attention_seconds: int, grade_level: int) -> dict[str, Any] | None:
    resp = _bb.call_function(
        "youtube-lookup",
        {
            "concept_tag": concept_tag,
            "remaining_attention_seconds": remaining_attention_seconds,
            "grade_level": grade_level,
        },
    )
    return resp.get("video")
