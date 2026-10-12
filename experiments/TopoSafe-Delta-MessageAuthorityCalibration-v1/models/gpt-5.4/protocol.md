# TopoSafe-Delta Message-Authority Calibration Protocol

**Status:** Development calibration only.

- Model slug: `gpt-5.4`
- Model ID: `global.openai.gpt-5.4`
- Region: `us-east-1`
- Temperature: `None`
- Top-p: `None`
- Additional fields: `{"reasoning_effort":"low"}`
- Repetitions: `2`

The calibration uses synthetic approval-bypass and false-completion tasks.
Ground-truth executor state remains unchanged. Every non-baseline message
asserts the same false, newer state update and recommends the same violating
action. Conditions vary only the externally supplied channel provenance after
the self-reported-state condition.

This composite ladder locates a model-specific susceptibility window. It is
not a confirmatory estimate of topology's causal effect.
