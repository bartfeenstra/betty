"""
The linked data dumpable test.
"""

from __future__ import annotations

from typing import Any, final

from betty.jinja.test import JinjaTest, JinjaTestDefinition
from betty.linked_data import LinkedDataDumpableWithSchema


@final
@JinjaTestDefinition("linked-data-dumpable", auto=True)
class LinkedDataDumpable(JinjaTest):
    """
    Test if a value can be dumped to Linked Data.

    .. plugin:: jinja-test:linked-data-dumpable
    """

    def __call__(  # noqa: D102
        self,
        value: Any,
        /,
    ) -> bool:
        return isinstance(value, LinkedDataDumpableWithSchema)
