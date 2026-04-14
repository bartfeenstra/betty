from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.warnings import BettyDeprecationWarning

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertTemplateString


async def test_deprecate(assert_template_string: AssertTemplateString) -> None:
    deprecation_message = "ye olde deprecation"
    with pytest.warns(BettyDeprecationWarning, match=deprecation_message):
        async with assert_template_string(
            template=f"{{% do deprecate('{deprecation_message}') %}}"
        ) as (_actual, _):
            pass
