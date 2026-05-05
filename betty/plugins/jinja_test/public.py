"""
The public test.
"""

from __future__ import annotations

from typing import Any, final

from betty.jinja.test import JinjaTest, JinjaTestDefinition
from betty.privacy.resolve import is_public


@final
@JinjaTestDefinition("public", auto=True)
class Public(JinjaTest):
    """
    Test if a value is public.

    .. plugin:: jinja-test:public
    """

    def __call__(  # noqa: D102
        self,
        value: Any,
        /,
    ) -> bool:
        return is_public(value)
