"""GitRepository — a particular repository, identity independent of its mutable name."""

from typing import Any, ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from tap_plugin.git_core.identity import HASH_ALGORITHMS

from tap_grid.models import BaseModel


class Repository(BaseModel):
    """A particular Git repository: the neutral node a forge's hosting record links to.

    Identity is the forge instance plus the forge's immutable repository id (``identity.py``),
    so a rename changes a field and a mirror on another host is a second repository. Hosting
    facts (owner, visibility, API configuration, collection observability) live on the forge
    plugin's hosting record, which links here with its own edge.

    Spec: specs/spec-git_core-v0.md (req-git-core-repository)
    """

    ENTITY_TYPE: ClassVar[str] = "git_core__git_repository"
    ENTITY_NAME: ClassVar[str] = "Git Repository"
    ENTITY_DESCRIPTION: ClassVar[str] = (
        "A Git repository, identified by its host and the host's immutable id — never by its name."
    )
    ENTITY_ICON: ClassVar[str] = "git-repository"
    DEFAULT_DIMENSIONS: ClassVar[dict[str, str]] = {"git.object": "repository"}
    DEFAULT_DISPLAY: ClassVar[dict[str, Any]] = {
        "tap_viz": {
            "shape": "round-rectangle",
            "colors": {"fill": "#FFFFFF", "border": "#F05033", "label": "#1F2328"},
        }
    }

    FIELD_CRUD_SCHEMA: ClassVar[dict[str, Any]] = {
        "forge": {"type": "string", "minLength": 1},
        "stable_id": {"type": "string", "minLength": 1},
        "name": {"type": "string"},
        "default_ref": {"type": "string"},
        "hash_algorithm": {"type": "string", "enum": list(HASH_ALGORITHMS)},
        "configuration": {"type": "object"},
        "tags": {"type": "object"},
    }
    FIELD_VALIDATION_SCHEMA: ClassVar[dict[str, Any]] = {
        "forge": {
            "validation": "jsonschema",
            "schema": {"type": "string", "minLength": 1},
        },
        "stable_id": {
            "validation": "jsonschema",
            "schema": {"type": "string", "minLength": 1},
        },
        "name": {"validation": "jsonschema", "schema": {"type": "string"}},
        "default_ref": {"validation": "jsonschema", "schema": {"type": "string"}},
        "hash_algorithm": {
            "validation": "jsonschema",
            "schema": {"type": "string", "enum": list(HASH_ALGORITHMS)},
        },
        "configuration": {"validation": "jsonschema", "schema": {"type": "object"}},
        "tags": {"validation": "jsonschema", "schema": {"type": "object"}},
    }
    CREATE_REQUIRED: ClassVar[list[str]] = ["forge", "stable_id"]

    # The host instance this repository lives on (github.com, gitlab.example.org, a synthetic
    # source's name) and that host's IMMUTABLE identifier for it — the two identity inputs.
    forge = models.CharField(max_length=255, blank=True, default="", db_index=True)
    stable_id = models.CharField(max_length=255, blank=True, default="", db_index=True)
    # Display name as the host shows it today; mutable, never part of the identity.
    name = models.CharField(max_length=255, blank=True, default="")
    # Full path of the default ref (refs/heads/main); "" when the host did not say.
    default_ref = models.CharField(max_length=512, blank=True, default="")
    hash_algorithm = models.CharField(max_length=16, blank=True, default="sha1")
    configuration = models.JSONField(default=dict, blank=True)
    tags = models.JSONField(default=dict, blank=True)

    class Meta(BaseModel.Meta):
        db_table = "git_core_git_repository"

    def validate(self) -> None:
        if self.default_ref and not self.default_ref.startswith("refs/"):
            raise ValidationError(
                {"default_ref": ["default_ref must be a full ref path (refs/...)"]}
            )

    def get_name(self) -> str:
        return self.name or (f"{self.forge}/{self.stable_id}" if self.forge else "")

    def __str__(self) -> str:
        return self.get_name()
