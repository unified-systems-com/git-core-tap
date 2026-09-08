"""Git Core — the neutral Git vocabulary.

Three nodes any source can mint — `git_repository`, `git_ref`, `git_commit` — and the three
relations between them (`DECLARES_REF`, `RESOLVES_COMMIT`, `STORES_COMMIT`), with identities derived
in `tap_plugin.git_core.identity` from facts that need no forge. Forge plugins (github_core)
observe this vocabulary and link their own hosting records and verification verdicts to it; this
package imports no forge and ships no collector. Spec: specs/spec-git_core-v0.md.
"""
