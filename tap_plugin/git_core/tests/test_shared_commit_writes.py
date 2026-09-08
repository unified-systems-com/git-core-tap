"""req-git-core-commit-2/-3 and the host-collision done-tests: many writers, one commit."""

from __future__ import annotations

import copy
from typing import Any

import pytest
import tap_plugin.git_core.models as git  # noqa: F401 — trigger model registration
from tap_plugin.git_core.fixtures.kernel import build_document, commit_oid
from tap_plugin.git_core.identity import (
    edge_id,
    git_commit_id,
    git_ref_id,
    git_repository_id,
)
from tap_plugin.git_core.models import Commit

from tap.pytest_harness import make_admin_user
from tap_grid.grift import grift_import
from tap_grid.models import Edge, Entity


def _second_source(
    batch_suffix: str, *, commit_overrides: dict[str, Any]
) -> dict[str, Any]:
    """Another host ('mirror.example') observing the kernel's c1 with its own facts."""
    oid = commit_oid("c1")
    cid = git_commit_id("sha1", oid)
    repo = git_repository_id("mirror.example", "m-1")
    ref = git_ref_id(repo, "refs/heads/main")
    commit_fields: dict[str, Any] = {
        "hash_algorithm": "sha1",
        "oid": oid,
        **commit_overrides,
    }
    doc = copy.deepcopy(build_document())
    batch = doc["batches"][0]
    batch["batch_entity"]["entity_id"] = str(
        edge_id("batch", repo, cid)
    )  # any stable, distinct id
    batch["batch_entity"]["name"] = f"mirror {batch_suffix}"
    batch["batch_node"]["name"] = f"mirror {batch_suffix}"
    batch["batch_node"]["source"] = "tests.mirror"
    batch["nodes"] = [
        {
            "entity": {
                "entity_id": str(repo),
                "entity_type": "git_core__git_repository",
                "name": "mirror",
                "dimensions": {},
            },
            "node": {"forge": "mirror.example", "stable_id": "m-1", "name": "mirror"},
        },
        {
            "entity": {
                "entity_id": str(ref),
                "entity_type": "git_core__git_ref",
                "name": "main",
                "dimensions": {},
            },
            "node": {
                "ref": "refs/heads/main",
                "ref_type": "branch",
                "name": "main",
                "head_sha": oid,
            },
        },
        {
            "entity": {
                "entity_id": str(cid),
                "entity_type": "git_core__git_commit",
                "name": oid[:12],
                "dimensions": {},
            },
            "node": commit_fields,
        },
    ]
    batch["edges"] = [
        {
            "entity": {
                "entity_id": str(edge_id("DECLARES_REF__git_core", repo, ref)),
                "entity_type": "edge",
                "name": "d",
                "dimensions": {},
            },
            "edge": {
                "from_entity_id": str(repo),
                "to_entity_id": str(ref),
                "edge_type": "DECLARES_REF__git_core",
                "properties": {},
            },
        },
        {
            "entity": {
                "entity_id": str(edge_id("STORES_COMMIT__git_core", repo, cid)),
                "entity_type": "edge",
                "name": "s",
                "dimensions": {},
            },
            "edge": {
                "from_entity_id": str(repo),
                "to_entity_id": str(cid),
                "edge_type": "STORES_COMMIT__git_core",
                "properties": {},
            },
        },
        {
            "entity": {
                "entity_id": str(edge_id("RESOLVES_COMMIT__git_core", ref, cid)),
                "entity_type": "edge",
                "name": "r",
                "dimensions": {},
            },
            "edge": {
                "from_entity_id": str(ref),
                "to_entity_id": str(cid),
                "edge_type": "RESOLVES_COMMIT__git_core",
                "properties": {},
            },
        },
    ]
    return doc


@pytest.mark.django_db
class TestOneCommitManyHosts:
    @pytest.mark.spec("req-git-core-commit-2")
    def test_a_degraded_second_source_cannot_blank_known_fields_and_membership_stays_separate(
        self,
    ) -> None:
        actor = make_admin_user("kernel-importer")
        assert grift_import(
            build_document(), dangling_edge_mode="strict", actor=actor
        ).success
        result = grift_import(
            _second_source(
                "degraded", commit_overrides={"author_name": "", "author_email": ""}
            ),
            dangling_edge_mode="strict",
            actor=actor,
        )
        assert result.success, result.errors
        cid = git_commit_id("sha1", commit_oid("c1"))
        commit = Commit.objects.get(entity_id=cid)
        assert (
            commit.author_email == "ada@kernel.example"
            and commit.author_name == "Ada Kernel"
        )
        assert (
            Entity.objects.filter(entity_type="git_core__git_commit", pk=cid).count()
            == 1
        ), "one commit"
        assert (
            Edge.objects.filter(
                edge_type="STORES_COMMIT__git_core", to_entity_id=cid
            ).count()
            == 2
        ), "two hosts store it"
        assert (
            Entity.objects.filter(entity_type="git_core__git_repository").count() == 2
        ), "two repositories, not one"

    @pytest.mark.spec("req-git-core-commit-3")
    def test_a_conflicting_intrinsic_fact_fails_loudly(self) -> None:
        actor = make_admin_user("kernel-importer")
        assert grift_import(
            build_document(), dangling_edge_mode="strict", actor=actor
        ).success
        result = grift_import(
            _second_source(
                "conflict", commit_overrides={"author_email": "someone-else@example"}
            ),
            dangling_edge_mode="strict",
            actor=actor,
        )
        assert not result.success
        assert any(
            "conflicting intrinsic fact" in str(e) for e in result.errors
        ), result.errors
        assert (
            Commit.objects.get(
                entity_id=git_commit_id("sha1", commit_oid("c1"))
            ).author_email
            == "ada@kernel.example"
        )

    @pytest.mark.spec("req-git-core-ref-1")
    def test_same_ref_path_in_two_repositories_is_two_refs(self) -> None:
        actor = make_admin_user("kernel-importer")
        assert grift_import(
            build_document(), dangling_edge_mode="strict", actor=actor
        ).success
        assert grift_import(
            _second_source("refs", commit_overrides={}),
            dangling_edge_mode="strict",
            actor=actor,
        ).success
        assert (
            Entity.objects.filter(entity_type="git_core__git_ref", name="main").count()
            == 2
        )


@pytest.mark.django_db
@pytest.mark.spec("req-git-core-commit-2")
def test_re_observing_the_same_commit_with_the_same_iso_dates_is_not_a_conflict() -> (
    None
):
    """The first live re-collection (2026-09-08) tripped the conflict rule on a date that had been
    stored as an aware datetime and arrived again as the same ISO string. Same fact, no conflict.
    """
    actor = make_admin_user("kernel-importer")
    assert grift_import(
        build_document(), dangling_edge_mode="strict", actor=actor
    ).success
    again = grift_import(
        _second_source(
            "again",
            commit_overrides={
                "authored_date": "2026-01-01T09:00:00Z",
                "committed_date": "2026-01-01T09:00:00Z",
            },
        ),
        dangling_edge_mode="strict",
        actor=actor,
    )
    assert again.success, again.errors
    from tap_grid.services import patch_node

    result = patch_node(
        str(git_commit_id("sha1", commit_oid("c1"))),
        {"authored_date": "2026-01-01T09:00:00Z"},
    )
    assert result.success, result.errors
