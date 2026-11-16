"""Remove the retired ``git.object`` dimension key from git_core's existing rows (George, 2026-11-16).

``git.object`` was dropped on 2026-09-20 (``req-git-core-dimensions-1``, git-core-tap#11): it restated the entity
type, and nothing has written it since. Rows created before that date still carry it. Core's dimension-map reshape
(unified-systems-com/tap#711, ``tap_grid`` 0012) stops on any key no installed seed declares, and this key is
deliberately not declared, so a grid holding such rows could not be upgraded until they were cleaned.

Why this touches the spine table: dimensions live on ``tap_entity.dimensions``, not on git_core's typed tables. The
statement is limited to git_core's own rows (node rows whose ``entity_type`` starts ``git_core__``, and edge rows,
whose spine ``entity_type`` is ``edge``, whose ``tap_edge.edge_type`` ends ``__git_core``) and to rows that carry the
key. It removes only that key and leaves every other dimension as it was. Run twice, it changes nothing the second
time. It runs on the name-keyed map, before core's reshape; on a map already keyed by node id it matches no row.

Upgrade order: install and migrate this git_core release while the grid is still on a core that predates the
reshape, then upgrade core. That is the order core's own migration states for plugin key changes ("plugin releases
first"). It is not encoded as ``run_before`` on core's migration, on purpose: that would make this migration a
dependency of one that grids already on the new core have applied, and Django refuses to migrate a database whose
applied migration has an unapplied dependency. On such a grid this migration finds nothing to do anyway.

Nothing is lost: the value was the row's type (``repository``, ``ref``, ``commit``, ``relation``), which the row
still states. Reversing is a no-op.
"""

from django.db import migrations

RETIRED_KEY = "git.object"

#: git_core's own node types share this prefix; its edge types end in this suffix (the edge's spine row is
#: entity_type "edge", so edges are found through tap_edge).
NODE_PREFIX = "git_core__"
EDGE_SUFFIX = "__git_core"

# A constant statement; every value is a bound parameter.
DROP = """
UPDATE tap_entity AS e
   SET dimensions = e.dimensions - %(old)s
 WHERE e.dimensions ? %(old)s
   AND (
        starts_with(e.entity_type, %(prefix)s)
     OR (e.entity_type = 'edge'
         AND EXISTS (SELECT 1 FROM tap_edge AS g
                      WHERE g.entity_id = e.id AND right(g.edge_type, %(suffix_len)s) = %(suffix)s))
   )
"""


def strip_git_object(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            DROP,
            {"old": RETIRED_KEY, "prefix": NODE_PREFIX, "suffix_len": len(EDGE_SUFFIX), "suffix": EDGE_SUFFIX},
        )


class Migration(migrations.Migration):
    dependencies = [
        ("git_core", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(strip_git_object, migrations.RunPython.noop),
    ]
