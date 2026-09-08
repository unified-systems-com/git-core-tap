"""req-git-core-kernel-fixture: a non-forge source populates the whole vocabulary; the JSON is derived."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import tap_plugin.git_core.models as git  # noqa: F401 — trigger model registration
from tap_plugin.git_core.fixtures.kernel import (
    DOCUMENT_PATH,
    build_document,
    commit_oid,
)
from tap_plugin.git_core.identity import git_commit_id, git_ref_id, git_repository_id

from tap.pytest_harness import make_admin_user
from tap_grid.grift import grift_import
from tap_grid.models import Edge, Entity

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


@pytest.mark.spec("req-git-core-kernel-fixture-1")
def test_committed_document_is_the_derived_document() -> None:
    assert (
        json.loads(DOCUMENT_PATH.read_text()) == build_document()
    ), "regenerate: python -m tap_plugin.git_core.fixtures.kernel"


@pytest.mark.spec("req-git-core-kernel-fixture-2")
def test_fixture_imports_nothing_from_a_forge() -> None:
    """Only stdlib and git_core: the emitter is a second source, not a forge in disguise."""
    import ast

    tree = ast.parse((FIXTURES_DIR / "kernel.py").read_text())
    modules = [
        getattr(node, "module", None) or a.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import | ast.ImportFrom)
        for a in node.names
    ]
    assert modules, "the emitter imports something"
    for module in modules:
        root = module.split(".")[0]
        assert root in {
            "__future__",
            "hashlib",
            "json",
            "pathlib",
            "typing",
            "uuid",
            "tap_plugin",
        }, module
        assert not module.startswith("tap_plugin.") or module.startswith(
            "tap_plugin.git_core"
        ), module


@pytest.mark.django_db
@pytest.mark.spec("req-git-core-kernel-fixture-1")
def test_import_populates_the_vocabulary_with_helper_minted_ids() -> None:
    result = grift_import(
        build_document(),
        dangling_edge_mode="strict",
        actor=make_admin_user("kernel-importer"),
    )
    assert result.success, result.errors
    assert Entity.objects.filter(entity_type="git_core__git_repository").count() == 1
    assert Entity.objects.filter(entity_type="git_core__git_ref").count() == 3
    assert Entity.objects.filter(entity_type="git_core__git_commit").count() == 3
    for edge_type, n in (
        ("DECLARES_REF__git_core", 3),
        ("RESOLVES_COMMIT__git_core", 3),
        ("STORES_COMMIT__git_core", 3),
    ):
        assert Edge.objects.filter(edge_type=edge_type).count() == n, edge_type
    repo = git_repository_id("kernel.example", "kernel-1")
    assert Entity.objects.filter(pk=repo).exists()
    assert Entity.objects.filter(pk=git_ref_id(repo, "refs/tags/v2")).exists()
    assert Entity.objects.filter(pk=git_commit_id("sha1", commit_oid("c3"))).exists()


@pytest.mark.django_db
@pytest.mark.spec("req-git-core-edges-2")
def test_annotated_tag_resolves_to_the_peeled_commit_while_naming_its_tag_object() -> (
    None
):
    from tap_plugin.git_core.fixtures.kernel import TAG_OBJECT_V2
    from tap_plugin.git_core.models import Ref

    assert grift_import(
        build_document(),
        dangling_edge_mode="strict",
        actor=make_admin_user("kernel-importer"),
    ).success
    repo = git_repository_id("kernel.example", "kernel-1")
    v2 = Ref.objects.get(entity_id=git_ref_id(repo, "refs/tags/v2"))
    assert (
        v2.target_sha == TAG_OBJECT_V2
        and v2.target_type == "tag"
        and v2.head_sha == commit_oid("c3")
    )
    edge = Edge.objects.get(
        edge_type="RESOLVES_COMMIT__git_core", from_entity_id=v2.entity_id
    )
    assert edge.to_entity_id == git_commit_id("sha1", commit_oid("c3"))
