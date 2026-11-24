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
        ("expected", "plugin_id", "data"),
        [
            (True, None, DummyPluginOne()),
            (True, DummyPluginOne.definition.id, DummyPluginOne()),
            (False, DummyPluginOne.definition.id, DummyPluginTwo()),
            (False, None, None),
            (False, None, object()),
        ],
    )
    async def test___call__(
        self, expected: bool, plugin_id: MachineName | None, data: Any
    ) -> None:
        sut = Plugin()
        assert sut(data, DummyPluginDefinition.definition.id, plugin_id) == expected
