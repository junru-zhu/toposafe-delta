# Direct Execution Topology Experiment Status

**Current status:** three-model technical sensitivity complete; four-model
technical completion blocked by the GPT-5.4 provider endpoint.

## Frozen primary design

- 60 fresh tasks with no prior task-ID overlap;
- four policy families and six operational domains;
- four role proposals, three authority regimes, and paired below-cut false /
  valid true worlds;
- 5,760 planned formal calls;
- seven deterministic execution layouts;
- one provider attempt per assigned call;
- USD 12 hard cap including smoke and technical recovery.

## Immutable parent collection

| Model | Rows | Provider errors | Malformed | Parent gate |
| --- | ---: | ---: | ---: | --- |
| Claude Sonnet 5 | 1,440 | 0 | 0 | pass |
| Llama 4 Maverick | 1,440 | 0 | 3 | pass |
| Nemotron 3 Super 120B | 1,440 | 7 | 4 | fail |
| GPT-5.4 | 12 recorded, then stopped | 10 | 0 | incomplete / fail |

The interrupted GPT block is stored under `aborted_provider_outage/` and is
excluded in full, including its two successful behavioral rows.

## Technical recovery

- v0.1R froze exactly the seven Nemotron provider-error IDs and recollected
  them successfully: 7/7, zero provider errors, zero malformed rows.
- v0.1R GPT longest-prompt smoke: 2/2 provider read timeouts at 240 seconds;
  no formal calls made.
- v0.1R2 GPT longest-prompt smoke: 2/2 provider read timeouts at 600 seconds;
  no formal calls made.
- Excluded compatibility probes through `us.openai.gpt-5.4` in `us-west-2`
  and the Bedrock Mantle Responses endpoint also reached 600-second transport
  timeouts. These probes are not experimental evidence.

The immutable parent gate remains failed and incomplete. Recovery never
retroactively changes that status.

## Available evidence

The zero-call three-model sensitivity validates:

- 4,320 complete role proposals;
- 7,560 deterministic execution-layout rows;
- zero provider errors after the seven exact Nemotron replacements;
- seven malformed rows retained as malformed;
- complete mediation gives zero invalid-proof executed FAR in every guarded
  layout;
- one uncovered source or executor edge restores large executable risk for
  Llama and Nemotron when those models propose protected actions;
- Claude proposes no invalid protected action in these cells, so bypass
  coverage has no executable effect for that model;
- capability distribution, single-holder placement, and valid-task utility
  remain model- and authority-regime-dependent.

This is not a four-model replication claim and is not yet manuscript evidence.

## Cost

- current public-list estimate from recorded successful usage: USD 5.7569;
- conservative accounting: USD 6.9083;
- hard cap: USD 12.

Provider timeouts that report no token usage add no model-token estimate here;
the AWS invoice remains the billing source of truth.

## Resume condition

Resume only after a longest-prompt GPT compatibility probe succeeds. Then:

1. freeze a new GPT-only technical-completion package against the exact parent
   and recovery hashes;
2. run the complete 1,440-row GPT block without using outcome-dependent
   selection;
3. validate all 5,760 proposal IDs and 10,080 deterministic layout rows;
4. run the original four-model bootstrap and equivalence rules;
5. integrate only the supported result into the manuscript.
