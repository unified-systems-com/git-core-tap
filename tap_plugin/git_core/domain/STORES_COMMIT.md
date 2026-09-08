# Stores Commit

## Blurb

A repository's object store holds this commit — observed presence, never complete history: the edge is emitted for every commit a source observed in that repository, and its absence means unobserved, not absent.

## Purpose

A repository's object store holds this commit. Emitted for every commit a source observed in that repository, so the edge means *observed present* — its absence means unobserved, never absent, and the set is never a complete history. This is the membership half of the commit's global identity: the commit node belongs to no repository, and two hosts storing the same commit produce two of these edges to one node.

## Goals

- One relation, one mechanism, no properties: the facts that would be properties live as field history on the nodes.

## Identity

One edge per (source, target) pair; the kernel fixture and every emitter mint envelope ids with `identity.edge_id`.

## Boundaries

Property-free by design; nothing on the edge names a host.

## Authoritative Source

- **Source:** Git — the reference and object model (`git-check-ref-format`, `gitglossary`: ref, commit object, annotated tag object, peeling)
- **Version:** Git 2.51 documentation (the object model has been stable since Git 1.x; SHA-256 object format per `gitformat-hash`)
- **Retrieved:** 2026-09-08

## Prior Art

- unified-systems-com/tap-plugin-github-core#76 rev 2 (2026-09-08) — the extraction rulings: identities, observation semantics, shared-write rules, edge names.
- `tap-plugin-github-core/specs/spec-github-core-vocabulary.md` — the concept rows this vocabulary was extracted from (`github_repository`, `git_ref`, `git_commit`, decision 2 on one ref type).
- Codex review of #76 (2026-09-08, off-issue) — ship the three neutral nodes together; ref identity from repository identity + full path; commit-observation identity concrete; no `TARGETS_OBJECT`.

## Neutrality

**Neutral.** Emitted by the kernel fixture without a forge; a forge plugin emits the same edge type for the same relation.

## Observability

Emitted when both endpoints were observed by the same source; absent means unobserved, never absent.

## Endpoints

- **Source:** `git_core__git_repository`
- **Target:** `git_core__git_commit`
- **Dimensions:** `git.object: relation`.
- **Properties:** none.
