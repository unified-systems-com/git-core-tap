"""Git Core plugin models package.

Class names are the plain nouns (Repository, Ref, Commit) rather than GitRef/GitCommit: the
entity spine's reverse accessor is derived from the class name, so a class named GitRef here
would clash with github_core's GitRef while the two plugins coexist (the transition of
github-core#76). Identity is ENTITY_TYPE (git_core__git_ref), never the class name.
"""

from tap_plugin.git_core.models.git_commit import Commit
from tap_plugin.git_core.models.git_ref import Ref
from tap_plugin.git_core.models.git_repository import Repository

__all__ = ["Commit", "Ref", "Repository"]
