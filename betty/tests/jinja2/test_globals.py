from __future__ import annotations

import pytest

from betty.test_utils.jinja2 import assert_template_string
from betty.typing import internal
from betty.warnings import BettyDeprecationWarning


@internal
async def test_deprecate() -> None:
    deprecation_message = "ye olde deprecation"
    with pytest.warns(BettyDeprecationWarning, match=deprecation_message):
        async with assert_template_string(
            template=f"{{% do deprecate('{deprecation_message}') %}}"
        ) as (actual, _):
            pass
