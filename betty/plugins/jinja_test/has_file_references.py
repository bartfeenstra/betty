"""
The has file references test.
"""

from __future__ import annotations

from typing import Any, final

from betty.entity.has_file_references import HasFileReferences as HasFileReferencesType
from betty.jinja.test import JinjaTest, JinjaTestDefinition


@final
@JinjaTestDefinition("has-file-references", auto=True)
class HasFileReferences(JinjaTest):
    """
    Test if a value has :py:class:`betty.entities.file_reference.FileReference` entities associated with it.

    .. plugin:: jinja-test:has-file-references
    """

    def __call__(  # noqa: D102
        self,
        value: Any,
        /,
    ) -> bool:
        return isinstance(value, HasFileReferencesType)
