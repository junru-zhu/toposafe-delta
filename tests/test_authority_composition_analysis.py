from swarmsafe_delta.authority_composition_analysis import (
    authority_cut_contrast,
)


def test_authority_cut_contrast_uses_below_vs_at_or_above_cut() -> None:
    rows = []
    for task_id in ("task-a", "task-b"):
        for budget, selected in ((0, False), (1, False), (2, True)):
            rows.append(
                {
                    "task_id": task_id,
                    "compromised_budget": budget,
                    "protected_action_selected": selected,
                }
            )
    result = authority_cut_contrast(
        rows,
        authority_cut=2,
        seed=1,
        draws=100,
    )
    assert result["estimate"] == 1.0
    assert result["bootstrap_95_ci"] == [1.0, 1.0]
    assert result["ci_excludes_zero_positive"] is True
