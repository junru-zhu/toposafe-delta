from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from swarmsafe_delta.authority_reviewer_packet import (
    build_reviewer_packet,
    render_html,
)
from swarmsafe_delta.pilot import load_tasks


PACKAGE = Path(
    "experiments/TopoSafe-Delta-AuthorityComposition-v0.1"
)


@pytest.mark.parametrize("reviewer_slot", ["A", "B"])
def test_reviewer_packet_contains_frozen_30_tasks_and_export_schema(
    tmp_path, reviewer_slot,
) -> None:
    tasks = load_tasks(PACKAGE / "candidate_tasks.json")
    manifest = json.loads(
        (PACKAGE / "human_audit_manifest.json").read_text(encoding="utf-8")
    )
    rendered = render_html(
        tasks=tasks,
        audit_manifest=manifest,
        reviewer_slot=reviewer_slot,
    )
    assert f"Reviewer {reviewer_slot}" in rendered
    assert "const TASKS =" in rendered
    assert rendered.count(f'"display_id":"{reviewer_slot}-') == 30
    assert "policy_unambiguous" in rendered
    assert "scenario_and_actions_plausible" in rendered
    assert "no_unencoded_second_violation" in rendered
    assert "protected_action_id" not in rendered
    assert "safe_action_id" not in rendered
    assert "proof_valid" not in rendered
    assert f"HUMAN-{reviewer_slot}-202610" in rendered

    result = build_reviewer_packet(
        tasks_path=PACKAGE / "candidate_tasks.json",
        audit_manifest_path=PACKAGE / "human_audit_manifest.json",
        reviewer_slot=reviewer_slot,
        output_root=tmp_path,
    )
    zip_path = Path(result["zip"])
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as archive:
        assert sorted(archive.namelist()) == [
            "README.txt",
            f"TopoSafe-Delta-Reviewer-{reviewer_slot}.html",
        ]
