"""GitCommit — a commit's content identity and intrinsic metadata, shared by every observer."""

from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from tap_plugin.git_core.identity import HASH_ALGORITHMS, OID_LENGTH

from tap_grid.models import BaseModel

_HEX = frozenset("0123456789abcdef")


class Commit(BaseModel):
    """A commit: hash algorithm + full object id, and what Git itself records about it.

    Global content identity (``identity.py``): the same commit observed from two hosts is ONE
    node. Only INTRINSIC facts live here — the object id, the two dates, author and committer
    name and email. Anything a forge observed about the commit (the login it resolved an email
    to, whether it verified a signature) belongs on that forge's observation node, linked to
    this one, never here; the schema rejects such keys.

    Shared-write rules (req-git-core-commit, ruling 0.3): several sources write this node, so a
    write that carries a BLANK for a field the node already holds keeps the held value (a
    degraded source cannot erase what a complete one recorded), and a write asserting a
    DIFFERENT non-blank value for an intrinsic field fails loudly naming both values — never
    last-writer-wins.

    Spec: specs/spec-git_core-v0.md (req-git-core-commit)
    """

    ENTITY_TYPE: ClassVar[str] = "git_core__git_commit"
    ENTITY_NAME: ClassVar[str] = "Git Commit"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A commit by content identity — hash algorithm and object id — with the author and "
        "committer facts Git itself records. One node however many hosts observe it."
    )
    ENTITY_ICON: ClassVar[str] = "git-commit"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"git.object": "commit"}
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "ellipse",
            "colors": {"fill": "#FFFFFF", "border": "#57606A", "label": "#1F2328"},
        }
    }

    #: Fields every source may assert and that must agree across sources.
    INTRINSIC_FIELDS: ClassVar[tuple[str, ...]] = (
        "hash_algorithm",
        "oid",
        "authored_date",
        "committed_date",
        "author_name",
        "author_email",
        "committer_name",
        "committer_email",
    )

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "hash_algorithm": {"type": "string", "enum": list(HASH_ALGORITHMS)},
        "oid": {"type": "string", "minLength": 40, "maxLength": 64},
        "authored_date": {"type": ["string", "null"], "format": "date-time"},
        "committed_date": {"type": ["string", "null"], "format": "date-time"},
        "author_name": {"type": "string"},
        "author_email": {"type": "string"},
        "committer_name": {"type": "string"},
        "committer_email": {"type": "string"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "hash_algorithm": {
            "validation": "jsonschema",
            "schema": {"type": "string", "enum": list(HASH_ALGORITHMS)},
        },
        "oid": {
            "validation": "jsonschema",
            "schema": {"type": "string", "minLength": 40, "maxLength": 64},
        },
        "author_name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "author_email": {"validation": "jsonschema", "schema": {"type": "string"}},
        "committer_name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "committer_email": {"validation": "jsonschema", "schema": {"type": "string"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["hash_algorithm", "oid"]

    hash_algorithm = models.CharField(
        max_length=16, blank=True, default="sha1", db_index=True
    )
    # Full object id, lower-case hex — with hash_algorithm, the identity.
    oid = models.CharField(max_length=64, blank=True, default="", db_index=True)
    authored_date = models.DateTimeField(null=True, blank=True)
    committed_date = models.DateTimeField(null=True, blank=True)
    author_name = models.CharField(max_length=255, blank=True, default="")
    author_email = models.CharField(max_length=255, blank=True, default="")
    committer_name = models.CharField(max_length=255, blank=True, default="")
    committer_email = models.CharField(max_length=255, blank=True, default="")

    class Meta(BaseModel.Meta):
        db_table = "git_core_git_commit"

    def validate(self) -> None:
        errors: dict[str, list[str]] = {}
        if self.hash_algorithm not in HASH_ALGORITHMS:
            errors["hash_algorithm"] = [
                f"unknown hash algorithm {self.hash_algorithm!r}"
            ]
        elif len(self.oid) != OID_LENGTH[self.hash_algorithm] or any(
            c not in _HEX for c in self.oid
        ):
            errors["oid"] = [
                f"oid must be a lower-case {OID_LENGTH[self.hash_algorithm]}-hex {self.hash_algorithm} object id"
            ]
        if errors:
            raise ValidationError(errors)
        self._reconcile_with_stored()

    def _reconcile_with_stored(self) -> None:
        """Shared-write rules against the persisted row (no-op on first write)."""
        if self._state.adding or self.pk is None:
            return
        stored = (
            type(self).objects.filter(pk=self.pk).values(*self.INTRINSIC_FIELDS).first()
        )
        if stored is None:
            return
        conflicts: dict[str, list[str]] = {}
        for field in self.INTRINSIC_FIELDS:
            model_field = self._meta.get_field(field)
            # Coerce both sides through the field: an incoming ISO string and the stored aware
            # datetime are the same fact, not a conflict (first live re-collection, 2026-09-08).
            held = model_field.to_python(stored[field])
            incoming = model_field.to_python(getattr(self, field))
            if incoming in ("", None) and held not in ("", None):
                setattr(
                    self, field, held
                )  # a degraded source cannot blank a known fact
            elif (
                held not in ("", None)
                and incoming not in ("", None)
                and incoming != held
            ):
                conflicts[field] = [
                    f"conflicting intrinsic fact: held {held!r}, incoming {incoming!r}"
                ]
        if conflicts:
            raise ValidationError(conflicts)

    def get_name(self) -> str:
        return self.oid[:12] if self.oid else ""

    def __str__(self) -> str:
        return self.get_name()
