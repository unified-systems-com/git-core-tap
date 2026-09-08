# Stores Commit

## Blurb

A repository's object store holds this commit — observed presence, never complete history: the edge is emitted for every commit a source observed in that repository, and its absence means unobserved, not absent.

## Purpose

A repository's object store holds this commit. Emitted for every commit a source observed in that repository, so the edge means *observed present* — its absence means unobserved, never absent, and the set is never a complete history. This is the membership half of the commit's global identity: the commit node belongs to no repository, and two hosts storing the same commit produce two of these edges to one node.

## Identity

One edge per `(source, target)` pair: `git_core__git_repository` → `git_core__git_commit`; the kernel fixture mints envelope ids with `identity.edge_id`.

## Boundaries

Property-free by design; `default_dimensions` is `{"git.object": "relation"}` and nothing names a host.

## Neutrality

**Neutral.** Emitted by the kernel fixture without a forge.
