# Direct Execution Topology Three-Model Technical Sensitivity

This zero-call analysis was created after the frozen parent GPT block was
interrupted by a provider outage and two independently frozen GPT recovery
smoke attempts also failed.

It uses:

- the immutable parent Claude block;
- the immutable parent Llama block;
- the immutable parent Nemotron block with exactly seven provider-error rows
  replaced by the frozen v0.1R technical recovery;
- no GPT behavioral rows;
- no failed smoke rows.

The original four-model large-effect and practical-equivalence rules are not
redefined. This analysis reports exact available-model effects and validates
the execution-topology instrument; it is not a four-model confirmatory result
and must not be used to claim cross-model replication.
