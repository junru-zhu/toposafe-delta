# TopoSafe-Delta Message-Mediation Pilot Protocol

**Status:** Development trajectory-fork diagnostic.

The executor is the only model call and the only node allowed to alter external
state. Every condition uses one delivered recommendation, the same tool
permissions, and the same action budget.

## Conditions

1. `direct_original`: original message with the exact executor prompt format
   used by the preceding role-placement pilot.
2. `hidden_relay_identical`: a logged one-hop route, but the executor receives
   the exact same prompt as `direct_original`.
3. `relay_verbatim`: original text with visible relay provenance.
4. `source_paraphrase`: frozen action-preserving paraphrase in the original
   executor prompt format.
5. `relay_paraphrase`: the same paraphrase with relay provenance.
6. `verifier_rewrite`: frozen policy-verifier message with verifier provenance.

The direct-versus-hidden-relay pair is a negative control for a graph path that
is not visible in executor context. The remaining conditions test provenance,
wording, and policy transformation.
