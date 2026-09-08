# Git Ref

## Blurb

A branch or tag: a full ref path in one repository and the commit it currently points at. Movement of a tag is the signal; movement of a branch is routine.

## Purpose

A ref is a name that moves. Rulesets protect one, caches are scoped to one, releases target one, and three of the incidents in github_core's corpus are a tag that moved under something that trusted it. The node exists so that "what does `v1` point at now, and what did it point at yesterday" is a field-history question on one row, and so a rule that protects `refs/heads/main` has a node to protect that no forge owns.

## Goals

- One type for branches and tags (`ref_type`), because a ruleset's target is one enum across both and a moved tag is the same detection as a moved branch.
- Identity by full path, so `refs/heads/release` and `refs/tags/release` never merge.
- Keep the peel explicit: `head_sha` is the commit; `target_sha`/`target_type` name the tag object when there is one.

## Identity

Natural key: **`<repository id>#<full ref path>`** — `identity.git_ref_id(repository, ref)`. The repository half is the neutral repository's id, never `owner/repo` (moved from github_core with that change, github-core#76). The same path in two repositories is two refs.

## Boundaries

- **Not the tag object.** An annotated tag's own signature and message are out of scope; `target_sha` records that it exists.
- **Not history.** The commit graph behind the head is not collected; `head_sha` history is the movement record.
- **Not remote-tracking or symbolic refs.** v0 covers `refs/heads/*` and `refs/tags/*`.

## Authoritative Source

- **Source:** Git — the reference and object model (`git-check-ref-format`, `gitglossary`: ref, commit object, annotated tag object, peeling)
- **Version:** Git 2.51 documentation (the object model has been stable since Git 1.x; SHA-256 object format per `gitformat-hash`)
- **Retrieved:** 2026-09-08

## Prior Art

- unified-systems-com/tap-plugin-github-core#76 rev 2 (2026-09-08) — the extraction rulings: identities, observation semantics, shared-write rules, edge names.
- `tap-plugin-github-core/specs/spec-github-core-vocabulary.md` — the concept rows this vocabulary was extracted from (`github_repository`, `git_ref`, `git_commit`, decision 2 on one ref type).
- Codex review of #76 (2026-09-08, off-issue) — ship the three neutral nodes together; ref identity from repository identity + full path; commit-observation identity concrete; no `TARGETS_OBJECT`.

## Neutrality

**Neutral.** Every Git host has refs with these exact semantics; the kernel fixture emits them without a forge.

## Observability

`head_sha` is what the source resolved at collection; a ref the source could not resolve is not emitted rather than emitted blank.

## Fields

- `ref` — the full path (`refs/heads/main`, `refs/tags/v1`): the identity input with the repository. Never the short name, because a branch and a tag may share one.
- `ref_type` — `branch` or `tag`, derived from the prefix and checked against it.
- `name` — the short name for display (`main`, `v1`); derivable from `ref`, kept for the label.
- `head_sha` — the PEELED commit the ref resolves to; `RESOLVES_COMMIT`'s target and, in field history, the record of every move.
- `target_sha` — the direct target when it is not the commit (an annotated tag's tag object); `""` when the ref points straight at the commit.
- `target_type` — `tag` when `target_sha` names a tag object, `commit` when a source reports the direct target explicitly, `""` otherwise; required whenever `target_sha` is set.
- `is_default` — whether this is the repository's default ref.
- `configuration` — JSONB residue for what a source returns that is not lifted into a column.
- `tags` — TAP's own tag map, uniform across every model.
