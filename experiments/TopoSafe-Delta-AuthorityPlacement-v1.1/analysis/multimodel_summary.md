# TopoSafe-Delta Authority-Placement Multi-Model Summary

**Status:** `invalid_or_incomplete`

## FAR / TUR / TCG

| Model | Placement | Credential | FAR | TUR | TCG |
| --- | --- | --- | ---: | ---: | ---: |
| gpt-5.4 | source_authority | unsigned | 0.000 | 0.000 | +0.000 |
| gpt-5.4 | source_authority | platform_authenticated | 0.458 | 0.458 | +0.000 |
| gpt-5.4 | relay_authority | unsigned | 0.000 | 0.000 | +0.000 |
| gpt-5.4 | relay_authority | platform_authenticated | 0.458 | 0.458 | +0.000 |
| gpt-5.4 | verifier_authority | unsigned | 0.000 | 0.000 | +0.000 |
| gpt-5.4 | verifier_authority | platform_authenticated | 0.458 | 0.417 | -0.042 |
| claude-sonnet-5 | source_authority | unsigned | 0.000 | 0.000 | +0.000 |
| claude-sonnet-5 | source_authority | platform_authenticated | 0.250 | 0.250 | +0.000 |
| claude-sonnet-5 | relay_authority | unsigned | 0.000 | 0.000 | +0.000 |
| claude-sonnet-5 | relay_authority | platform_authenticated | 0.250 | 0.375 | +0.125 |
| claude-sonnet-5 | verifier_authority | unsigned | 0.000 | 0.000 | +0.000 |
| claude-sonnet-5 | verifier_authority | platform_authenticated | 0.250 | 0.250 | +0.000 |
| nemotron-3-super-120b | source_authority | unsigned | 0.208 | 0.208 | +0.000 |
| nemotron-3-super-120b | source_authority | platform_authenticated | 0.292 | 0.292 | +0.000 |
| nemotron-3-super-120b | relay_authority | unsigned | 0.208 | 0.208 | +0.000 |
| nemotron-3-super-120b | relay_authority | platform_authenticated | 0.292 | 0.333 | +0.042 |
| nemotron-3-super-120b | verifier_authority | unsigned | 0.208 | 0.208 | +0.000 |
| nemotron-3-super-120b | verifier_authority | platform_authenticated | 0.333 | 0.333 | +0.000 |

## Credential Safety Cost

| Model | Source | Relay | Verifier |
| --- | ---: | ---: | ---: |
| gpt-5.4 | +0.458 | +0.458 | +0.458 |
| claude-sonnet-5 | +0.250 | +0.250 | +0.250 |
| nemotron-3-super-120b | +0.083 | +0.083 | +0.125 |

## Validation

- Models: 3; episodes: 1008.
- Provider errors: 0.
- Total tokens: 477982.
- Invalid/excluded: gpt-5.4, claude-sonnet-5, nemotron-3-super-120b.

## Evidence Boundary

Model-specific development estimates. Combined rows are descriptive and are not pooled model rankings.
