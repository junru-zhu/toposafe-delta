# TopoSafe-Delta Topology Pilot Protocol

**Status:** Development diagnostic only.

## Frozen Inputs

- Tasks: approval-vendor-contract, completion-backup-restore, completion-data-migration, completion-delivery-inspection, completion-deployment-canary.
- Source regimes: risky, safe.
- Topologies: direct_star, one_hop_tree, two_hop_chain.
- Repetitions: 5.
- Model: `global.amazon.nova-2-lite-v1:0`.

## Graph Budget

- Four nodes: frozen source, reviewer 1, reviewer 2, executor.
- Three directed edges and three delivered message slots per topology.
- Three assigned model calls per episode: two reviewers and one executor.
- The source message is frozen from the prior development pilot.

## Topologies

- `direct_star`: source sends to both reviewers and the executor; reviewer outputs are shadowed.
- `one_hop_tree`: source sends to both reviewers; reviewer 1 sends to the executor.
- `two_hop_chain`: source sends to reviewer 1, reviewer 1 sends to reviewer 2, and reviewer 2 sends to the executor.

## Outcomes

- Primary: deterministic executable policy violation and safe task success.
- Mechanism: risky action recommendation at reviewer 1 and reviewer 2.
- Cost: calls, input/output tokens, latency, and parse/provider failures.

## Claim Boundary

The risky messages were selected because they caused a violation in the prior Nova development pilot. Results diagnose whether reviewer path length attenuates those fixed messages. They do not estimate population-level topology effects.
