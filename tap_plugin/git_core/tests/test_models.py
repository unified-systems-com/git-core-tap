"""The three neutral nodes through the service layer: contract, dimensions, names, no forge fields."""

from __future__ import annotations

from typing import Any

import pytest
import tap_plugin.git_core.models as git  # noqa: F401 — trigger model registration

from tap_grid.models import Entity
from tap_grid.services import create_node

OID = "b" * 40


def _create(type_slug: str, payload: dict[str, Any]) -> Entity:
    result = create_node(type_slug, payload)
    assert result.success, f"create_node failed: {result.errors}"
    return Entity.objects.get(pk=result.entity_id)


@pytest.mark.django_db
class TestRepository:
    @pytest.mark.spec("req-git-core-repository-2")
    def test_create_dimension_and_name(self) -> None:
        e = _create(
            "git_core__git_repository",
            {"forge": "kernel.example", "stable_id": "1", "name": "kernel"},
        )
        assert e.dimensions == {"git.object": "repository"} and e.name == "kernel"

    @pytest.mark.spec("req-git-core-repository-1")
    def test_name_is_not_identity_and_default_ref_is_a_full_path(self) -> None:
        e = _create(
            "git_core__git_repository", {"forge": "kernel.example", "stable_id": "2"}
        )
        assert e.name == "kernel.example/2"
        bad = create_node(
            "git_core__git_repository",
            {"forge": "x", "stable_id": "3", "default_ref": "main"},
        )
        assert not bad.success


@pytest.mark.django_db
class TestRef:
    @pytest.mark.spec("req-git-core-ref-1")
    def test_full_path_type_agreement_and_short_name(self) -> None:
        e = _create(
            "git_core__git_ref",
            {"ref": "refs/tags/v1", "ref_type": "tag", "head_sha": OID},
        )
        assert e.dimensions == {"git.object": "ref"} and e.name == "v1"
        assert not create_node(
            "git_core__git_ref", {"ref": "refs/tags/v1", "ref_type": "branch"}
        ).success
        assert not create_node(
            "git_core__git_ref", {"ref": "v1", "ref_type": "tag"}
        ).success

    @pytest.mark.spec("req-git-core-ref-1")
    def test_annotated_tag_keeps_the_peel_explicit(self) -> None:
        assert not create_node(
            "git_core__git_ref",
            {"ref": "refs/tags/v2", "ref_type": "tag", "target_sha": "c" * 40},
        ).success
        e = _create(
            "git_core__git_ref",
            {
                "ref": "refs/tags/v2",
                "ref_type": "tag",
                "head_sha": OID,
                "target_sha": "c" * 40,
                "target_type": "tag",
            },
        )
        assert e.name == "v2"


@pytest.mark.django_db
class TestCommit:
    @pytest.mark.spec("req-git-core-commit-1")
    def test_create_dimension_and_short_name(self) -> None:
        e = _create(
            "git_core__git_commit",
            {
                "hash_algorithm": "sha1",
                "oid": OID,
                "author_email": "ada@kernel.example",
            },
        )
        assert e.dimensions == {"git.object": "commit"} and e.name == OID[:12]

    @pytest.mark.spec("req-git-core-commit-4")
    def test_forge_fields_are_rejected(self) -> None:
        for key in ("author_login", "signature_state", "signed_by_github"):
            result = create_node(
                "git_core__git_commit", {"hash_algorithm": "sha1", "oid": OID, key: "x"}
            )
            assert not result.success, key

    @pytest.mark.spec("req-git-core-commit-1")
    def test_oid_must_match_the_algorithm(self) -> None:
        assert not create_node(
            "git_core__git_commit", {"hash_algorithm": "sha1", "oid": "d" * 64}
        ).success
        assert not create_node(
            "git_core__git_commit", {"hash_algorithm": "sha256", "oid": "d" * 40}
        ).success
        assert create_node(
            "git_core__git_commit", {"hash_algorithm": "sha256", "oid": "d" * 64}
        ).success
