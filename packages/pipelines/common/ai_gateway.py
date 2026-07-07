"""Butterbase AI-gateway client with a deterministic local fallback.

Every LLM node in the three pipelines routes through :func:`generate` instead of
calling a provider SDK directly — that is the plan's "AI gateway routes LLM calls"
requirement (§3 Butterbase), with fast/strong model tiers chosen per task.

Locally (no ``BUTTERBASE_AI_GATEWAY_URL`` configured, or an injected fake) it returns
deterministic, well-formed output so the pipelines run and can be stress-tested
offline. When the gateway URL is set it POSTs to Butterbase, which does the real
model routing. Person A owns the gateway; Person B owns which task uses which tier.
"""

from __future__ import annotations

import json
from typing import Any

from . import providers
from .config import settings

# Task -> model tier. Fast for extraction/scoring, strong for generation/synthesis.
_STRONG_TASKS = {"game_code_repair", "replan_level_code", "report_narrative"}


def _model_for(task: str) -> str:
    return settings.model_strong if task in _STRONG_TASKS else settings.model_fast


def generate(task: str, *, system: str | None = None, context: dict[str, Any] | None = None) -> Any:
    """Run an LLM task through the gateway. Returns a str or dict depending on task.

    An injected ``ai_gateway`` provider (a callable ``(task, system, context) -> Any``)
    wins first — used by tests to assert prompts. Otherwise, if the gateway URL is
    configured we POST to Butterbase; else we fall back to a deterministic local
    generator so offline runs still produce valid pipeline output.
    """
    context = context or {}

    override = providers._overrides.get("ai_gateway")
    if override is not None:
        return override(task, system, context)

    if settings.ai_gateway_url:
        return _remote(task, system, context)

    return _local(task, context)


def _remote(task: str, system: str | None, context: dict[str, Any]) -> Any:
    bb = providers.get_butterbase()
    resp = bb.call_function(
        "ai-gateway",
        {"task": task, "model": _model_for(task), "system": system, "context": context},
    )
    return resp.get("output")


def _local(task: str, context: dict[str, Any]) -> Any:
    """Deterministic offline generation, one branch per LLM task in the pipelines."""
    if task == "game_code_repair":
        # The critic "fixes" the code; the sandbox validates on the next attempt.
        code = context.get("code", "")
        stderr = (context.get("stderr", "") or "").splitlines()[:1]
        note = stderr[0] if stderr else "runtime error"
        return f"{code}\n# critic-repair: addressed {note}\n"

    if task == "replan_level_code":
        idx = context.get("level_index", 0)
        strategy = context.get("strategy", "reorder")
        return (
            f"# level_{idx}.py — regenerated for strategy={strategy}\n"
            f"from templates import build_level\n"
            f"LEVEL = build_level({json.dumps(context.get('level_spec', {}))})\n"
        )

    if task == "report_narrative":
        summ = context.get("session_summary", {})
        bottleneck = context.get("bottleneck_concept", "")
        completed = summ.get("levels_completed", 0)
        total = summ.get("levels_total", 0)
        parent = (
            f"Your child completed {completed} of {total} levels today. "
            f"They stayed engaged and pushed through the tricky parts. "
            f"{('We noticed ' + bottleneck + ' is worth a little extra practice.') if bottleneck else 'Great, balanced session.'}"
        )
        doctor = (
            f"Session shows {summ.get('replan_count', 0)} replan(s) and a "
            f"completion rate of {summ.get('completion_rate', 0)}. "
            f"Primary concept bottleneck: {bottleneck or 'none identified'}. "
            f"Attention held across the arc; recommend targeted follow-up on the bottleneck concept."
        )
        return {
            "parent_summary": parent,
            "doctor_narrative": doctor,
            "start_with_concept": context.get("start_with_concept", ""),
        }

    if task == "assignment_metadata":
        # Deterministic scoring lives in game_spec.score_assignment; this branch
        # exists so a remote gateway can override it without changing call sites.
        return context

    raise ValueError(f"unknown ai_gateway task: {task!r}")
