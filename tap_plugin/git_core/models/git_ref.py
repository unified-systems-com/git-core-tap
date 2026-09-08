"""GitRef — a full named reference in a repository and the commit it currently resolves to."""

from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models

from tap_grid.models import BaseModel

_HEX = frozenset("0123456789abcdef")


class Ref(BaseModel):
    """A branch or tag: a full ref path and the commit it points at, in one repository.

    Moved from github_core with its contract intact (github-core#76): identity by full path so
    ``refs/heads/release`` and ``refs/tags/release`` differ; ``head_sha`` is the PEELED commit
    while ``target_sha``/``target_type`` record the direct target when it differs (an annotated
    tag's tag object); movement is field history on ``head_sha``. Branch and tag are one type
    (vocabulary decision 2, 2026-08-27). ``owner/repo`` is gone: the repository is the
    ``DECLARES_REF`` source and the identity input.

    Spec: specs/spec-git_core-v0.md (req-git-core-ref)
    """

    ENTITY_TYPE: ClassVar[str] = "git_core__git_ref"
    ENTITY_NAME: ClassVar[str] = "Git Ref"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A branch or tag — a full ref path and the commit it points at. Movement of a tag is the "
        "signal; movement of a branch is routine."
    )
    ENTITY_ICON: ClassVar[str] = "git-ref"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"git.object": "ref"}
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#8250DF", "label": "#1F2328"},
        }
    }

    REF_TYPE_BRANCH = "branch"
    REF_TYPE_TAG = "tag"
    TARGET_TYPE_COMMIT = "commit"
    TARGET_TYPE_TAG = "tag"

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "ref": {"type": "string", "minLength": 1},
        "ref_type": {"type": "string", "enum": [REF_TYPE_BRANCH, REF_TYPE_TAG]},
        "name": {"type": "string"},
        "head_sha": {"type": "string"},
        "target_sha": {"type": "string"},
        "target_type": {
            "type": "string",
            "enum": ["", TARGET_TYPE_COMMIT, TARGET_TYPE_TAG],
        },
        "is_default": {"type": "boolean"},
        "configuration": {"type": "object"},
        "tags": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "ref": {
            "validation": "jsonschema",
            "schema": {"type": "string", "minLength": 1},
        },
        "ref_type": {
            "validation": "jsonschema",
            "schema": {"type": "string", "enum": [REF_TYPE_BRANCH, REF_TYPE_TAG]},
        },
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "head_sha": {"validation": "jsonschema", "schema": {"type": "string"}},
        "target_sha": {"validation": "jsonschema", "schema": {"type": "string"}},
        "target_type": {
            "validation": "jsonschema",
            "schema": {
                "type": "string",
                "enum": ["", TARGET_TYPE_COMMIT, TARGET_TYPE_TAG],
            },
        },
        "is_default": {"validation": "jsonschema", "schema": {"type": "boolean"}},
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
        "tags": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["ref", "ref_type"]

    # Full path — the identity input. refs/heads/<branch> or refs/tags/<tag>.
    ref = models.CharField(max_length=512, blank=True, default="", db_index=True)
    ref_type = models.CharField(max_length=16, blank=True, default="", db_index=True)
    # Short name (main, v1.2.0) for display; derivable from `ref`, kept for the label.
    name = models.CharField(max_length=512, blank=True, default="")
    # The PEELED commit this ref resolves to — RESOLVES_COMMIT's target. Field history here is
    # where a moved tag becomes visible.
    head_sha = models.CharField(max_length=64, blank=True, default="", db_index=True)
    # The direct target when it is not the commit (an annotated tag's tag object); "" when the
    # ref points straight at the commit.
    target_sha = models.CharField(max_length=64, blank=True, default="")
    target_type = models.CharField(max_length=16, blank=True, default="")
    is_default = models.BooleanField(default=False)
    configuration = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "git_core_git_ref"

    def validate(self) -> None:
        errors: dict[str, list[str]] = {}
        if not self.ref.startswith("refs/"):
            errors["ref"] = [
                "ref must be a full path (refs/heads/... or refs/tags/...)"
            ]
        elif (
            self.ref.startswith("refs/heads/") and self.ref_type != self.REF_TYPE_BRANCH
        ):
            errors["ref_type"] = [f"refs/heads/* is a branch, not {self.ref_type!r}"]
        elif self.ref.startswith("refs/tags/") and self.ref_type != self.REF_TYPE_TAG:
            errors["ref_type"] = [f"refs/tags/* is a tag, not {self.ref_type!r}"]
        for field in ("head_sha", "target_sha"):
            value = getattr(self, field)
            if value and (value != value.lower() or any(c not in _HEX for c in value)):
                errors[field] = [f"{field} must be a lower-case hex object id"]
        if self.target_sha and not self.target_type:
            errors["target_type"] = ["target_type is required when target_sha is set"]
        if errors:
            raise ValidationError(errors)

    def get_name(self) -> str:
        if self.name:
            return self.name
        return (
            self.ref.removeprefix("refs/heads/").removeprefix("refs/tags/")
            if self.ref
            else ""
        )

    def __str__(self) -> str:
        return self.get_name()
