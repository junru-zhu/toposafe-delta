# Execution Topology Pilot v0.1R GPT Technical Recovery

The immutable parent pilot completed 512 assigned rows, but six GPT-5.4 rows
ended in Amazon Bedrock `ReadTimeoutError` after the frozen single attempt.
The parent four-model technical gate remains failed.

This separately identified sensitivity selects exactly and only parent rows
with `provider_error=true`. It makes one additional call per selected row with
the same task, prompt, model endpoint, output ceiling, schedule seed,
concurrency, timeout, and single-attempt policy. The six failed episode IDs and
the parent raw-file SHA-256 are frozen before recovery calls.

Recovered rows may be used only in a combined technical-recovery sensitivity.
They do not overwrite the parent raw file and do not retroactively make the
original primary run pass. The parent plus recovery remains subject to the
same cumulative USD 10 hard cap.

