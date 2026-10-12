# Direct Execution Topology v0.1R2 GPT Technical Completion

## Trigger

The first technical-completion package made no formal GPT calls because both
longest-prompt smoke calls reached the frozen 240-second client read timeout.
The parent GPT collection remains excluded and incomplete.

Historical successful GPT calls under the same model configuration had a
development-pilot mean latency of about 83 seconds, a 95th percentile near
167 seconds, and a maximum near the prior 180-second timeout. The consecutive
240-second failures are therefore treated as a provider-availability and
client-timeout compatibility problem, not as behavioral evidence.

## Frozen amendment

R2 freezes exactly one technical change:

- client read timeout: 240 seconds to 600 seconds.

The following remain unchanged:

- all 60 tasks and 1,440 GPT proposal cases;
- model ID and region;
- prompts, action spaces, role assignments, authority regimes, and worlds;
- reasoning configuration;
- 100-token output cap;
- one provider attempt per assigned call;
- schedule seed;
- deterministic recomposition and analysis.

Ten workers are used. Two longest-prompt calls are excluded smoke tests. The
formal block runs only if both smoke calls succeed without malformed or
truncated output.

## Combined sensitivity

If the complete GPT block passes, the combined sensitivity uses:

- parent Claude and Llama;
- parent Nemotron with the seven v0.1R technical replacements;
- the complete R2 GPT block;
- no interrupted parent GPT behavioral rows;
- no failed smoke rows.

The original parent technical gate remains failed and incomplete.
