from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from betty.jinja_tests.plugin import Plugin
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
            (True, DummyPluginOne.definition.id, DummyPluginOne()),
            (False, DummyPluginOne.definition.id, DummyPluginTwo()),
            (False, None, None),
            (False, None, object()),
        ],
    )
    async def test___call__(
        self, expected: bool, plugin_identifier: MachineName | None, data: Any
    ) -> None:
        sut = Plugin(DummyPluginDefinition)
        assert sut(data, plugin_identifier) == expected
