"""Domain-article coverage for git_core — `specs/spec-domain-articles.md`.

Every registered type, edge and dimension owes an article with the required sections, and every
`FIELD_CRUD_SCHEMA` key owes a line under `## Fields`. The same scanner core runs; this test is the
plugin's own gate so a new field cannot land undocumented.
"""

from __future__ import annotations

from pathlib import Path

import tap_plugin.git_core.models as git  # noqa: F401 — trigger model registration
from tap.domain_articles import findings_for_root

PACKAGE_ROOT = Path(__file__).resolve().parent.parent


def test_every_registered_type_has_a_conforming_article() -> None:
    findings = findings_for_root(PACKAGE_ROOT)
    assert not findings, "\n".join(str(f) for f in findings)
