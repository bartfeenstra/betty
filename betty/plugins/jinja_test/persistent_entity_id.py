"""
The persistent entity ID test.
"""

from __future__ import annotations

from typing import Any, final

from betty.jinja.test import JinjaTest, JinjaTestDefinition
from betty.model import persistent_id


@final
@JinjaTestDefinition("persistent-entity-id", auto=True)
class PersistentEntityId(JinjaTest):
    """
    Test if a value is a persistent entity ID.

    .. plugin:: jinja-test:persistent-entity-id
    """

    def __call__(  # noqa: D102
        self,
        value: Any,
        /,
    ) -> bool:
        return persistent_id(value)
