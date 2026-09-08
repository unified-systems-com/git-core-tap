# Declares Ref

## Blurb

A repository contains a named reference — a branch or a tag.

## Purpose

A repository contains a named reference. The edge is the containment half of the ref's identity (repository id + path); it carries nothing, because what a ref does — move — is field history on the ref's `head_sha`, and a property here would be a second, disagreeing copy.

Moved from github_core (github-core#76): the source is now the neutral repository, so a rule protecting a ref or a cache scoped to one can traverse to it without a forge in the path.

## Identity

One edge per `(source, target)` pair: `git_core__git_repository` → `git_core__git_ref`; the kernel fixture mints envelope ids with `identity.edge_id`.

## Boundaries

Property-free by design; `default_dimensions` is `{"git.object": "relation"}` and nothing names a host.

## Neutrality

**Neutral.** Emitted by the kernel fixture without a forge.
