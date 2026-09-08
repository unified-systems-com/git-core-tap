# Resolves Commit

## Blurb

A ref resolves to its PEELED commit — the branch head, or for an annotated tag the commit the tag object points at (the tag object itself stays a field on the ref: target_sha/target_type).

## Purpose

A ref resolves to its PEELED commit — the branch head, or for an annotated tag the commit the tag object points at. The tag object itself stays a field on the ref (`target_sha`/`target_type`): the naming rule forbids `_TO` and the object model excludes tag objects, so there is no `TARGETS_OBJECT`, and this one edge carries the peel explicitly. Replaces github_core's `POINTS_AT`.

Property-free: a moved ref re-derives the relation (shape G) and every write carries batch provenance, so an `observed_at` here would be a second derivation of a fact the grid already keeps.

## Identity

One edge per `(source, target)` pair: `git_core__git_ref` → `git_core__git_commit`; the kernel fixture mints envelope ids with `identity.edge_id`.

## Boundaries

Property-free by design; `default_dimensions` is `{"git.object": "relation"}` and nothing names a host.

## Neutrality

**Neutral.** Emitted by the kernel fixture without a forge.
