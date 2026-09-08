"""Git Core identity helpers — the ONE derivation of every git_core entity id (req-git-core-identity).

Every id is ``uuid5(GIT_CORE_NAMESPACE, "<entity_type>:<natural key>")`` over facts a non-GitHub
emitter also has: a repository is its forge instance plus the forge's immutable repository id
(never its display name); a ref is its repository's id plus its full path (never ``owner/repo``);
a commit is its hash algorithm plus its full object id (never a repository). github_core and the
kernel fixture both import these; nothing re-derives them.
"""

from __future__ import annotations

from uuid import NAMESPACE_DNS, UUID, uuid5

GIT_CORE_NAMESPACE: UUID = uuid5(NAMESPACE_DNS, "git_core.tap")

HASH_ALGORITHMS: tuple[str, ...] = ("sha1", "sha256")
#: Object-id length per algorithm (hex characters).
OID_LENGTH: dict[str, int] = {"sha1": 40, "sha256": 64}


def _id(entity_type: str, natural_key: str) -> UUID:
    return uuid5(GIT_CORE_NAMESPACE, f"{entity_type}:{natural_key}")


def git_repository_id(forge: str, stable_id: str) -> UUID:
    """Identity of a repository: ``<forge instance>/<the forge's immutable repository id>``.

    ``forge`` is the host instance (``github.com``, ``gitlab.example.org``, or a synthetic
    source's name); ``stable_id`` is that host's immutable identifier for the repository
    (GitHub's numeric ``id``, as a string). A rename never re-mints; a GitHub repository and
    its GitLab mirror never merge.
    """
    if not forge or not stable_id:
        raise ValueError("git_repository_id needs a non-empty forge and stable_id")
    return _id("git_core__git_repository", f"{forge}/{stable_id}")


def git_ref_id(repository: UUID, ref: str) -> UUID:
    """Identity of a ref: the repository's id plus the FULL ref path (``refs/heads/main``).

    ``refs/heads/release`` and ``refs/tags/release`` are distinct; the same path in two
    repositories is distinct.
    """
    if not ref.startswith("refs/"):
        raise ValueError(f"git_ref_id needs a full ref path (refs/...), got {ref!r}")
    return _id("git_core__git_ref", f"{repository}#{ref}")


def git_commit_id(hash_algorithm: str, oid: str) -> UUID:
    """Identity of a commit: ``<algorithm>:<full object id, lower-cased>`` — global content identity.

    Repository membership is the ``STORES_COMMIT`` edge, never part of the key, so the same
    commit observed from two hosts is one node.
    """
    if hash_algorithm not in HASH_ALGORITHMS:
        raise ValueError(f"git_commit_id: unknown hash algorithm {hash_algorithm!r}")
    oid_l = oid.lower()
    if len(oid_l) != OID_LENGTH[hash_algorithm] or any(
        c not in "0123456789abcdef" for c in oid_l
    ):
        raise ValueError(f"git_commit_id: {oid!r} is not a {hash_algorithm} object id")
    return _id("git_core__git_commit", f"{hash_algorithm}:{oid_l}")


def edge_id(edge_type: str, source: UUID, target: UUID) -> UUID:
    """Deterministic id for a git_core edge envelope in a GRIFT bundle (one per endpoint pair)."""
    return _id("edge", f"{edge_type}:{source}:{target}")
