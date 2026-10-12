# Execution Topology Pilot Budget Summary

As of 2026-10-12, this experiment used 526 provider attempts:

- 8 excluded smoke calls;
- 512 immutable parent formal calls, including 6 GPT-5.4 read timeouts;
- 6 separately frozen GPT-5.4 technical-recovery calls.

Recorded successful responses used 384,952 input tokens and 14,421 output
tokens. The current official-list-price estimate is USD 0.6342. Preserving the
frozen pre-call 10% allowance for GPT-5.4 and Claude Sonnet 5 gives USD 0.6941.
Conservative accounting is USD 0.8330, or 8.33% of the frozen USD 10 hard cap.

| Component | Official-list estimate | Frozen allowance estimate | Conservative cost |
| --- | ---: | ---: | ---: |
| Excluded smoke | $0.0101 | $0.0111 | $0.0133 |
| Immutable parent formal | $0.6184 | $0.6769 | $0.8123 |
| GPT technical recovery | $0.0056 | $0.0062 | $0.0074 |
| Total | $0.6342 | $0.6941 | $0.8330 |

| Formal sensitivity model | Cost range |
| --- | ---: |
| GPT-5.4 | $0.1637–$0.1800 |
| Claude Sonnet 5 | $0.4265–$0.4691 |
| NVIDIA Nemotron 3 Super 120B | $0.0110 |
| Llama 4 Maverick | $0.0229 |

The lower estimate uses current public list prices and AWS guidance that
global cross-region routing has no surcharge. The upper estimate preserves the
frozen pre-call allowance. Anthropic's August 10 changelog says the Sonnet 5
introductory price became permanent, while some older pricing documentation
still shows the superseded September increase. The AWS invoice and AWS
Marketplace line items are the final source of truth.
