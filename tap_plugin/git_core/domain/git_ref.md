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

## Neutrality

**Neutral.** Every Git host has refs with these exact semantics; the kernel fixture emits them without a forge.

## Observability

`head_sha` is what the source resolved at collection; a ref the source could not resolve is not emitted rather than emitted blank.
