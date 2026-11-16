"""Migration 0002 removes the retired ``git.object`` key from git_core's own rows and nothing else."""

from __future__ import annotations

import contextlib
import importlib
from types import SimpleNamespace

import pytest
from django.db import connection

from tap_grid.models import Entity

try:  # core main guards direct spine writes; tap 0.3.4 and earlier have no guard to lift
    from tap_grid.write_guard import unguarded_write
except ImportError:  # pragma: no cover - which branch runs depends on the installed core
    unguarded_write = contextlib.nullcontext

MIGRATION = "tap_plugin.git_core.migrations.0002_strip_retired_git_object"


def _legacy_row(entity_type: str, name: str, dimensions: dict[str, str]) -> Entity:
    """A spine row carrying a name-keyed dimensions map, as rows written before core's reshape do. The map is set
    with a queryset update: core main refuses a retired key on save, and an old row never went through that save."""
    row = Entity.objects.create(entity_type=entity_type, name=name)
    Entity.objects.filter(pk=row.pk).update(dimensions=dimensions)
    return row


@pytest.mark.django_db
@pytest.mark.spec("req-git-core-dimensions-4")
def test_the_migration_strips_git_object_from_git_core_rows_only() -> None:
    migration = importlib.import_module(MIGRATION)
    with unguarded_write():
        ours = _legacy_row("git_core__git_ref", "main", {"git.object": "ref", "git.host": "github.com"})
        theirs = _legacy_row("github_core__github_repository", "r", {"git.object": "repository"})
        untouched = _legacy_row("git_core__git_commit", "c", {"git.host": "github.com"})
        # An edge's spine row is entity_type "edge"; whose edge it is lives on tap_edge.edge_type.
        our_edge = _legacy_row("edge", "e1", {"git.object": "relation", "git.host": "github.com"})
        their_edge = _legacy_row("edge", "e2", {"git.object": "relation"})
    with connection.cursor() as cursor:
        for edge, edge_type in ((our_edge, "DECLARES_REF__git_core"), (their_edge, "HOSTS_REPOSITORY__github_core")):
            cursor.execute(
                "INSERT INTO tap_edge (batch_id, flip_map, edge_type, properties, entity_id, from_entity_id, to_entity_id)"
                " VALUES (%s, '{}', %s, '{}', %s, %s, %s)",
                ["test", edge_type, edge.pk, ours.pk, theirs.pk],
            )
    for _ in range(2):  # a second run changes nothing
        migration.strip_git_object(None, SimpleNamespace(connection=connection))
    for row in (ours, theirs, untouched, our_edge, their_edge):
        row.refresh_from_db()
    assert ours.dimensions == {"git.host": "github.com"}, "only the retired key goes"
    assert our_edge.dimensions == {"git.host": "github.com"}
    assert untouched.dimensions == {"git.host": "github.com"}
    assert theirs.dimensions == {"git.object": "repository"}, "another plugin's rows are not git_core's to change"
    assert their_edge.dimensions == {"git.object": "relation"}
