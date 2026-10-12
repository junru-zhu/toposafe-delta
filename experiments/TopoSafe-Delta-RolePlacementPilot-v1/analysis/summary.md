# TopoSafe-Delta Role-Placement Pilot

**Status:** Development diagnostic only.

- Valid episodes: 90/90.
- Tasks: 5.
- Validation passed: True.

| Source | Placement | Episodes | Violations | Violation rate | Task success | Relay risky | Verifier risky | Mean tokens |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| risky | direct_source | 15 | 14 | 0.933 | 1.000 | 15 | 0 | 845.1 |
| risky | relay_on_path | 15 | 5 | 0.333 | 1.000 | 15 | 0 | 826.9 |
| risky | verifier_on_path | 15 | 0 | 0.000 | 1.000 | 15 | 0 | 825.7 |
| safe | direct_source | 15 | 0 | 0.000 | 1.000 | 0 | 0 | 803.1 |
| safe | relay_on_path | 15 | 0 | 0.000 | 1.000 | 0 | 0 | 798.1 |
| safe | verifier_on_path | 15 | 0 | 0.000 | 1.000 | 0 | 0 | 794.0 |

## Paired Contrasts Against Direct Source

| Source | Treated placement | Pairs | Risk difference | Task-cluster bootstrap 95% CI |
| --- | --- | ---: | ---: | --- |
| risky | relay_on_path | 15 | -0.600 | [-1.000, -0.067] |
| risky | verifier_on_path | 15 | -0.933 | [-1.000, -0.800] |
| safe | relay_on_path | 15 | 0.000 | [0.000, 0.000] |
| safe | verifier_on_path | 15 | 0.000 | [0.000, 0.000] |

## Evidence Boundary

Outcome-selected development role-placement pilot. The relay and verifier prompts intentionally implement different node functions; this is not a pure graph-structure estimate.
