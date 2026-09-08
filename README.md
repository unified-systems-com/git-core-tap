# git-core-tap

The neutral Git vocabulary for [TAP](https://github.com/unified-systems-com/tap): repositories,
refs and commits with identities **any source can mint**. Forges observe this vocabulary — GitHub
through `github_core`, which emits it and links its own hosting records and verification verdicts to
it. This package owns it and imports no forge.

## What this plugin owns

- **`git_repository`** — a particular repository, identified by its host and the host's immutable
  id, never by its name. A rename is a field change; a mirror on another host is another repository.
- **`git_ref`** — a branch or tag: a full ref path in one repository and the commit it resolves to.
  `head_sha` is the peeled commit; `target_sha`/`target_type` name an annotated tag's tag object.
  Movement is field history.
- **`git_commit`** — content identity (`hash_algorithm` + full `oid`) and what Git itself records:
  the dates and the author/committer name and email. One node however many hosts observe it.
  Shared-write rules: a degraded source cannot blank a known field; a conflicting fact fails loudly.
- **Edges** — `DECLARES_REF` (repository → ref), `RESOLVES_COMMIT` (ref → peeled commit),
  `STORES_COMMIT` (repository → commit, *observed presence*, never complete history).
- **Identity helpers** — `tap_plugin.git_core.identity`: the one derivation of every id.
- **The kernel fixture** — `fixtures/kernel.py` + `kernel.grift.json`: a synthetic non-forge
  repository that populates the whole vocabulary through the identity helpers alone.
- **Dimension** — `git.object` ∈ repository | ref | commit | relation; nothing names a host.

## What lives elsewhere

- **github_core** — the GitHub hosting record, the collector, and `commit_observation` (resolved
  logins, signature verdicts). Depends on this plugin.
- **identity_core** — principals, credential grants, OIDC issuers.
- Pull requests, workflows/runs/jobs, packages and artifacts: other vocabularies, deliberately.

## Read first

- `specs/spec-git_core-v0.md` — the contract, one requirement per node, edge and rule.
- `tap_plugin/git_core/domain/*.md` — one article per type, edge and dimension.
- The extraction epic: unified-systems-com/tap-plugin-github-core#76.

## Install and validate

Add to a boot profile's `install` section (a substrate: list it before anything that depends on it):

```json
{ "slug": "git_core", "enabled": true, "source": { "type": "editable", "path": "_dev-plugins/git_core" } }
```

No population step: this plugin seeds nothing. Then, in a core checkout:
`uv run python -m tap.preboot --profile <profile>` (gates), `manage.py migrate`, `manage.py plugins`
(the report), and `pytest --pyargs tap_plugin.git_core` (the shipped suite, kernel fixture included).
Structure-only, no Django: `python -m tap_plugins.validate_plugin tap_plugin/git_core`.
