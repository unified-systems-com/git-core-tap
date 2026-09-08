# `git.object`

## Blurb

Which kind of Git object a row is — `repository`, `ref`, `commit` — or that it is a `relation` between them. The one partition key the neutral Git vocabulary carries.

## Purpose

A scoped query over a mixed grid wants "every ref" or "every commit" without knowing which forge observed them. `git.object` answers that from the dimension alone. It is the only key on these rows on purpose: the forge is a fact about the observer, and the observer's nodes (a hosting record, a commit observation) carry their own `github.*` keys; stamping the substrate with a forge would assert an ownership it does not have.

## Goals

- Partition the three neutral node kinds and their relations with one key.
- Name nothing about any host.

## Identity

The key is `git.object`, in the `git.` namespace this plugin owns; effectively immutable, as every dimension key is. Values are the four words above — Git's own nouns for its own objects, plus `relation` for the edges, so a reader who knows Git predicts the value without this article.

## Boundaries

- **Not the forge.** Which host observed a row is on the observer's nodes and edges (`github.platform` in github_core), never here.
- **Not declared-versus-executed.** The substrate is entirely declarations; there is nothing to partition.
- **Not the ref kind.** Branch versus tag is the `ref_type` field on the ref, a property, not a partition.

## Neutrality

**Neutral by construction.** A synthetic non-forge source (the kernel fixture) stamps the same values; nothing in the key or its values would change for another host.

## Observability

**Declared, never fetched**, applied at creation from type and edge-type defaults.
