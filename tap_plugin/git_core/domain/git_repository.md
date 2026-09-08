# Git Repository

## Blurb

A particular repository, identified by its host and the host's immutable id — never by its name. The neutral node a forge's hosting record links to, and the source of every ref and every stored commit.

## Purpose

Every Git question starts from a repository, and every forge has its own record of one: GitHub's carries an owner, a visibility, an API configuration and what a credential could observe. Those are hosting facts. What is neutral is narrower: that a repository exists on some host, what that host calls it today, which ref it treats as default, and which hash algorithm its object ids use. This node is that narrower thing, so a consumer that only cares about Git can traverse from it without reading a forge's vocabulary, and a forge view can still reach its hosting record through the forge's own link.

## Goals

- Give refs and commits a repository to belong to that no forge owns.
- Survive a rename: identity is the host's immutable id, so the name is a field that changes, not a node that reappears.
- Keep a mirror distinct: the same content on two hosts is two repositories that happen to agree.

## Identity

Natural key: **`<forge>/<stable_id>`** — the host instance plus that host's immutable repository identifier (GitHub's numeric `id`; a second source supplies its own). Entity id is `uuid5(git_core ns, "git_core__git_repository:<forge>/<stable_id>")` (`identity.git_repository_id`). Never `owner/name`, which is mutable and reassignable.

## Boundaries

Deliberately **not** covered:

- **Ownership, visibility, URLs, permissions, collection observability.** Hosting facts on the forge's hosting record.
- **Forks and networks.** A fork is another repository; the relation between them is the forge's to assert.
- **Content.** No trees, no blobs, no history; refs and stored commits are the observed edges of it.

## Neutrality

**Neutral.** The kernel fixture populates it from a synthetic source with no forge in the loop.

## Observability

Every field is what the observing source reported at collection; `default_ref` is `""` when the source did not say.
