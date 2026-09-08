# Git Commit

## Blurb

A commit by content identity — hash algorithm and full object id — with the author and committer facts Git itself records. One node however many hosts observe it.

## Purpose

A commit is the same object wherever it lives, and the questions that join on it — which refs resolve here, which runs built it, which repositories store it — want one node. github_core's earlier commit node keyed on repository + sha because GitHub's *verification verdict* is per repository network and a global key let one network's verdict overwrite another's. The resolution (github-core#76, ruling 0.1/0.2) is to split the two facts: the commit's intrinsic metadata is global and lives here; a forge's observation of it — resolved logins, signature verdict — lives on the forge's `commit_observation` node, one per host and repository, linked to this one. Nothing observed can overwrite anything intrinsic, and no verdict can overwrite another.

## Goals

- One node per `(hash_algorithm, oid)` across every source.
- Hold only what Git records: object id, two dates, author and committer name and email.
- Survive many writers: a degraded source cannot blank a known fact; a conflicting fact fails loudly.

## Identity

Natural key: **`<hash_algorithm>:<oid>`** (`identity.git_commit_id`), oid lower-cased. Repository membership is the `STORES_COMMIT` edge, never part of the key.

## Boundaries

Deliberately **not** covered:

- **Message, tree, parents.** Not history, not content.
- **Anything a forge resolved or judged.** Logins, `signed_by_*`, signature kind/state/validity — the forge's observation node; the schema here rejects those keys.
- **Signature payloads.** Bulk with no question behind them.

## Neutrality

**Neutral.** The kernel fixture emits commits with no forge; GitHub emits the same node for the same oid.

## Observability

Blank fields mean the source did not report them; a second source may fill them, and once filled they cannot be blanked (the shared-write rules in the model).
