from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.plugins.jinja_test.plugin import Plugin
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginTwo,
)

if TYPE_CHECKING:
    from betty.machine_name import MachineName


class TestPlugin:
    @pytest.mark.parametrize(
        ("expected", "plugin_identifier", "data"),
        [
            (True, None, DummyPluginOne()),
            (True, DummyPluginOne.plugin().id, DummyPluginOne()),
            (False, DummyPluginOne.plugin().id, DummyPluginTwo()),
            (False, None, None),
            (False, None, object()),
        ],
    )
    async def test___call__(
        self, expected: bool, plugin_identifier: MachineName | None, data: Any
    ) -> None:
        sut = Plugin(DummyPluginDefinition)
        assert sut(data, plugin_identifier) == expected
