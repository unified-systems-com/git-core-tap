"""The kernel fixture — a synthetic, non-forge source that populates the whole git_core vocabulary.

The vocabulary spec's kernel test made concrete (req-git-core-kernel-fixture): one repository on a
host that is not GitHub, a default branch, a lightweight tag, an annotated tag with its own tag
object, and three commits, emitted as a GRIFT document through ``git_core.identity`` and nothing
else. It proves the substrate is populatable by a second source, and it is the substrate for the
shared-write and host-collision tests. Deterministic: ``build_document()`` always returns the same
document, and the committed ``kernel.grift.json`` IS that document (a test asserts equality, so the
JSON can never drift from the code that derives it).

Regenerate: ``python -m tap_plugin.git_core.fixtures.kernel`` (inside the container).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import UUID, uuid5

from tap_plugin.git_core.identity import (
    GIT_CORE_NAMESPACE,
    edge_id,
    git_commit_id,
    git_ref_id,
    git_repository_id,
)

FORGE = "kernel.example"
STABLE_ID = "kernel-1"
VERSION = "v0.1.0"
DOCUMENT_PATH = Path(__file__).with_name("kernel.grift.json")


def _oid(label: str) -> str:
    """A deterministic sha1 object id for a labelled synthetic object."""
    return hashlib.sha1(
        f"git_core.kernel:{label}".encode(), usedforsecurity=False
    ).hexdigest()


#: The three commits, oldest first, and the annotated tag's tag object.
COMMITS: tuple[dict[str, str], ...] = (
    {
        "label": "c1",
        "authored_date": "2026-01-01T09:00:00Z",
        "author_name": "Ada Kernel",
        "author_email": "ada@kernel.example",
    },
    {
        "label": "c2",
        "authored_date": "2026-01-02T09:00:00Z",
        "author_name": "Ada Kernel",
        "author_email": "ada@kernel.example",
    },
    {
        "label": "c3",
        "authored_date": "2026-01-03T09:00:00Z",
        "author_name": "Bo Kernel",
        "author_email": "bo@kernel.example",
    },
)
TAG_OBJECT_V2 = _oid("tag-v2")


def commit_oid(label: str) -> str:
    return _oid(label)


def _node(
    entity_id: UUID, entity_type: str, name: str, fields: dict[str, Any]
) -> dict[str, Any]:
    return {
        "entity": {
            "entity_id": str(entity_id),
            "entity_type": entity_type,
            "name": name,
            "dimensions": {},
        },
        "node": fields,
    }


def _edge(edge_type: str, source: UUID, target: UUID, name: str) -> dict[str, Any]:
    return {
        "entity": {
            "entity_id": str(edge_id(edge_type, source, target)),
            "entity_type": "edge",
            "name": name,
            "dimensions": {},
        },
        "edge": {
            "from_entity_id": str(source),
            "to_entity_id": str(target),
            "edge_type": edge_type,
            "properties": {},
        },
    }


def build_document() -> dict[str, Any]:
    """The kernel repository as one GRIFT batch: 1 repository, 3 refs, 3 commits, 9 edges."""
    repo_id = git_repository_id(FORGE, STABLE_ID)
    nodes: list[dict[str, Any]] = [
        _node(
            repo_id,
            "git_core__git_repository",
            "kernel",
            {
                "forge": FORGE,
                "stable_id": STABLE_ID,
                "name": "kernel",
                "default_ref": "refs/heads/main",
                "hash_algorithm": "sha1",
            },
        )
    ]
    edges: list[dict[str, Any]] = []
    commit_ids: dict[str, UUID] = {}
    for c in COMMITS:
        oid = commit_oid(c["label"])
        cid = git_commit_id("sha1", oid)
        commit_ids[c["label"]] = cid
        nodes.append(
            _node(
                cid,
                "git_core__git_commit",
                oid[:12],
                {
                    "hash_algorithm": "sha1",
                    "oid": oid,
                    "authored_date": c["authored_date"],
                    "committed_date": c["authored_date"],
                    "author_name": c["author_name"],
                    "author_email": c["author_email"],
                    "committer_name": c["author_name"],
                    "committer_email": c["author_email"],
                },
            )
        )
        edges.append(
            _edge(
                "STORES_COMMIT__git_core",
                repo_id,
                cid,
                f"kernel STORES_COMMIT {oid[:12]}",
            )
        )

    refs: tuple[tuple[str, str, str, str, str, bool], ...] = (
        # (full path, ref_type, name, peeled commit label, tag object oid or "", is_default)
        ("refs/heads/main", "branch", "main", "c3", "", True),
        (
            "refs/tags/v1",
            "tag",
            "v1",
            "c2",
            "",
            False,
        ),  # lightweight: points straight at the commit
        (
            "refs/tags/v2",
            "tag",
            "v2",
            "c3",
            TAG_OBJECT_V2,
            False,
        ),  # annotated: the tag object is the direct target
    )
    for ref, ref_type, name, peeled, tag_object, is_default in refs:
        rid = git_ref_id(repo_id, ref)
        nodes.append(
            _node(
                rid,
                "git_core__git_ref",
                name,
                {
                    "ref": ref,
                    "ref_type": ref_type,
                    "name": name,
                    "head_sha": commit_oid(peeled),
                    "target_sha": tag_object,
                    "target_type": "tag" if tag_object else "",
                    "is_default": is_default,
                },
            )
        )
        edges.append(
            _edge("DECLARES_REF__git_core", repo_id, rid, f"kernel DECLARES_REF {ref}")
        )
        edges.append(
            _edge(
                "RESOLVES_COMMIT__git_core",
                rid,
                commit_ids[peeled],
                f"{ref} RESOLVES_COMMIT {commit_oid(peeled)[:12]}",
            )
        )

    batch_id = uuid5(GIT_CORE_NAMESPACE, f"batch:kernel-fixture:{VERSION}")
    return {
        "metadata": {"grift_version": "0"},
        "_reserved": {},
        "batches": [
            {
                "batch_entity": {
                    "entity_id": str(batch_id),
                    "entity_type": "batch",
                    "name": f"git_core kernel fixture {VERSION}",
                    "dimensions": {},
                },
                "batch_node": {
                    "source": "tap_plugin.git_core.fixtures.kernel",
                    "name": f"git_core kernel fixture {VERSION}",
                    "description": (
                        "A synthetic non-forge repository populating the whole git_core vocabulary through "
                        "git_core.identity alone (req-git-core-kernel-fixture): one repository on kernel.example, "
                        "refs/heads/main, a lightweight tag v1, an annotated tag v2 with its own tag object, three "
                        "commits; DECLARES_REF, RESOLVES_COMMIT and STORES_COMMIT for each. Not seeded by any product "
                        "record; imported by the plugin's tests and by anyone proving a second source."
                    ),
                },
                "nodes": nodes,
                "edges": edges,
            }
        ],
    }


def write_document(path: Path = DOCUMENT_PATH) -> None:
    path.write_text(
        json.dumps(build_document(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    write_document()
    print(f"wrote {DOCUMENT_PATH}")
