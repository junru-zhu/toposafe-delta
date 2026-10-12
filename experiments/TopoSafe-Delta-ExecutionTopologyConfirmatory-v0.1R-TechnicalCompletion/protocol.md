# Direct Execution Topology v0.1R Technical Completion Protocol

## Trigger

The frozen parent collection encountered a provider outage:

- the Nemotron parent block completed 1,440 assigned rows with seven
  `provider_error=true` rows;
- the GPT block was stopped after an outage pattern produced ten technical
  failures among twelve recorded rows;
- the complete interrupted GPT block is excluded, including its two successful
  behavioral rows.

The parent technical gate remains failed and incomplete.

## Frozen recovery selection

Before recovery calls:

1. freeze the parent manifest and proposal-case hashes;
2. freeze the complete Nemotron raw parent hash;
3. freeze the interrupted GPT raw hash;
4. select exactly the seven Nemotron parent IDs where
   `provider_error=true`;
5. select all 1,440 parent GPT proposal cases;
6. do not inspect action outcomes when selecting recovery rows.

The recovery makes 1,447 formal calls. Two longest-prompt smoke calls per
recovered model are excluded from formal evidence.

## Settings

- same task, prompt, action, model, inference, and output-cap settings as the
  parent;
- maximum one provider attempt per assigned call;
- six workers to reduce synchronized provider pressure;
- same schedule seed;
- the USD 12 hard cap covers parent, interrupted GPT attempts, smoke, and
  recovery successful-token accounting.

## Combined sensitivity

The combined technical-completion sensitivity uses:

- immutable parent Claude rows;
- immutable parent Llama rows;
- immutable parent Nemotron rows with exactly seven technical rows replaced by
  the frozen recovery responses;
- the complete recovery GPT block;
- none of the interrupted GPT behavioral rows.

All 5,760 expected proposal IDs, uniqueness, factorial balance, provider
status, malformed/truncated rate, deterministic layout recomposition, and
task-bootstrap analysis must be revalidated.

This recovery does not retroactively make the parent technical gate pass.
