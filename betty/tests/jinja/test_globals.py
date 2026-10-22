from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from betty.warnings import BettyDeprecationWarning

if TYPE_CHECKING:
    from betty.test_utils.conftest import AssertJinja


async def test_deprecate(assert_jinja_str: AssertJinja) -> None:
    deprecation_message = "ye olde deprecation"
    with pytest.warns(BettyDeprecationWarning, match=deprecation_message):
        async with assert_jinja_str(f"{{% do deprecate('{deprecation_message}') %}}"):
            pass
