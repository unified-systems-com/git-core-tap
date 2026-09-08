"""req-git-core-identity: ids derive from forge-free facts; a rename re-mints nothing; one commit per oid."""

from __future__ import annotations

import re
from pathlib import Path
from uuid import UUID

import pytest
from tap_plugin.git_core.identity import (
    git_commit_id,
    git_ref_id,
    git_repository_id,
)

OID = "a" * 40


@pytest.mark.spec("req-git-core-identity-1")
def test_repository_identity_is_forge_plus_stable_id_never_name() -> None:
    a = git_repository_id("github.com", "12345")
    assert isinstance(a, UUID) and a == git_repository_id("github.com", "12345")
    assert a != git_repository_id(
        "gitlab.example.org", "12345"
    ), "a mirror on another host is another repository"
    assert a != git_repository_id("github.com", "12346")


@pytest.mark.spec("req-git-core-identity-1")
def test_ref_identity_is_repository_plus_full_path() -> None:
    repo_a, repo_b = git_repository_id("kernel.example", "1"), git_repository_id(
        "kernel.example", "2"
    )
    assert git_ref_id(repo_a, "refs/heads/release") != git_ref_id(
        repo_a, "refs/tags/release"
    )
    assert git_ref_id(repo_a, "refs/heads/x") != git_ref_id(repo_b, "refs/heads/x")
    with pytest.raises(ValueError, match="full ref path"):
        git_ref_id(repo_a, "main")


@pytest.mark.spec("req-git-core-identity-1")
def test_commit_identity_is_algorithm_plus_oid_case_insensitive_and_repository_free() -> (
    None
):
    assert git_commit_id("sha1", OID) == git_commit_id("sha1", OID.upper())
    assert git_commit_id("sha1", OID) != git_commit_id("sha256", "a" * 64)
    with pytest.raises(ValueError):
        git_commit_id("sha1", "not-hex")
    with pytest.raises(ValueError):
        git_commit_id("md5", OID)


@pytest.mark.spec("req-git-core-identity-2")
def test_nothing_forge_shaped_in_the_helpers() -> None:
    """No forge import, no forge-shaped argument: the prose may say 'GitHub', the code may not need it."""
    import ast
    import inspect

    from tap_plugin.git_core import identity

    tree = ast.parse(
        (Path(__file__).resolve().parent.parent / "identity.py").read_text()
    )
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
            assert not any(
                re.search(r"github|gitlab|forge", n, re.IGNORECASE) for n in names
            ), names
    for fn in (git_repository_id, git_ref_id, git_commit_id):
        params = list(inspect.signature(fn).parameters)
        assert not any(
            re.search(r"login|owner|full_name|url|github", p, re.IGNORECASE)
            for p in params
        ), (fn.__name__, params)
    assert isinstance(
        identity.GIT_CORE_NAMESPACE, UUID
    )  # a constant, derived from no host
