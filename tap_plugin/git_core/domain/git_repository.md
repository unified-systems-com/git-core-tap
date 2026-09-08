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

## Authoritative Source

- **Source:** Git — the reference and object model (`git-check-ref-format`, `gitglossary`: ref, commit object, annotated tag object, peeling)
- **Version:** Git 2.51 documentation (the object model has been stable since Git 1.x; SHA-256 object format per `gitformat-hash`)
- **Retrieved:** 2026-09-08

## Prior Art

- unified-systems-com/tap-plugin-github-core#76 rev 2 (2026-09-08) — the extraction rulings: identities, observation semantics, shared-write rules, edge names.
- `tap-plugin-github-core/specs/spec-github-core-vocabulary.md` — the concept rows this vocabulary was extracted from (`github_repository`, `git_ref`, `git_commit`, decision 2 on one ref type).
- Codex review of #76 (2026-09-08, off-issue) — ship the three neutral nodes together; ref identity from repository identity + full path; commit-observation identity concrete; no `TARGETS_OBJECT`.

## Neutrality

**Neutral.** The kernel fixture populates it from a synthetic source with no forge in the loop.

## Observability

Every field is what the observing source reported at collection; `default_ref` is `""` when the source did not say.

## Fields

- `forge` — the host instance this repository lives on (`github.com`, `gitlab.example.org`, a synthetic source's name): half the identity.
- `stable_id` — that host's IMMUTABLE identifier for the repository (GitHub's numeric `id`, as a string): the other half. A rename never changes it.
- `name` — the display name as the host shows it today; mutable, never part of the identity.
- `default_ref` — the full path of the default ref (`refs/heads/main`); `""` when the source did not say.
- `hash_algorithm` — `sha1` or `sha256`: the object-id format this repository's commits use.
- `configuration` — JSONB residue for what a source returns that is not lifted into a column.
- `tags` — TAP's own tag map, uniform across every model.
