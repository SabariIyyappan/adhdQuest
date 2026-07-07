"""Pipeline 1 — Ingestion & Game Generation (plan §5).

Trigger: Butterbase webhook on PDF upload completion.
Wires the node sequence: OCR -> NER -> metadata LLM -> Cognee recall ->
game-spec LLM -> Daytona build -> Butterbase output. The canvas registers this
`run` as the pipeline entrypoint; nodes live in ../nodes for isolated testing.
"""

from __future__ import annotations

from typing import Any

from ..common import providers
from ..nodes import cognee_nodes, daytona_node, ner_node, ocr_node
from . import game_spec, prompts


def run(request: dict[str, Any]) -> dict[str, Any]:
    """Contract A in -> Contract B out.

    request = {child_id, assignment_id, pdf_storage_url, child_profile}
    """
    child_id = request["child_id"]
    assignment_id = request["assignment_id"]
    profile = request["child_profile"]

    # 1. OCR
    ocr = ocr_node.run(request["pdf_storage_url"])

    # 2. NER — tag questions
    questions = ner_node.run(ocr.raw_text)

    # 3. Assignment metadata (fast model)
    metadata = game_spec.score_assignment(questions)

    # 4. Cognee recall — prior behavioral context (empty on first session)
    prior_context = cognee_nodes.recall(child_id)

    # 5. Game spec (strong model + curriculum RAG + prior context)
    spec = game_spec.generate(
        questions=questions,
        metadata=metadata,
        prior_context=prior_context,
        profile=profile,
    )

    # 6. Daytona — build, validate, get preview URL
    game_code = prompts.render_game_code(spec)
    build = daytona_node.build_game(spec, game_code)

    # 7. Output — persist + realtime push (see output.py)
    from . import output

    return output.publish(
        bb=providers.get_butterbase(),
        child_id=child_id,
        assignment_id=assignment_id,
        spec=spec,
        build=build,
    )
