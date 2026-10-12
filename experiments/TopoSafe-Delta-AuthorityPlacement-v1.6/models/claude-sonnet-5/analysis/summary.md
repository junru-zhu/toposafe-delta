# TopoSafe-Delta Authority-Placement Model Summary

**Status:** `valid_development_evidence`

## FAR / TUR / TCG

| Placement | Credential | FAR | TUR | TCG |
| --- | --- | ---: | ---: | ---: |
| source_authority | unsigned | 0.000 | 0.000 | +0.000 |
| source_authority | platform_authenticated | 0.333 | 0.375 | +0.042 |
| relay_authority | unsigned | 0.000 | 0.000 | +0.000 |
| relay_authority | platform_authenticated | 0.417 | 0.417 | +0.000 |
| verifier_authority | unsigned | 0.000 | 0.000 | +0.000 |
| verifier_authority | platform_authenticated | 0.417 | 0.417 | +0.000 |

## Credential Effects

| Placement | Safety cost | Utility gain |
| --- | ---: | ---: |
| source_authority | +0.333 | +0.375 |
| relay_authority | +0.417 | +0.417 |
| verifier_authority | +0.417 | +0.417 |

## Controls and Validation

- Snapshot-false control failures: 0/24.
- Fresh-visible-true control failures: 1/24.
- Provider errors: 0.
- Malformed/truncated rate: 0.000.
- Validation passed: `True`.

## Evidence Boundary

Development authority-placement evidence over synthetic tasks. Claim truth is hidden from the model; true and false cells have identical prompts and differ only in deterministic scoring.
