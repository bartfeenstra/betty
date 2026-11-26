from __future__ import annotations

from importlib.metadata import EntryPoint, EntryPoints
from typing import TYPE_CHECKING

from betty.discoverers.entry_point import EntryPointDiscoverer
from betty.discoverers.module import (
    DefinitionDiscoverer,
    HasDefinitionDiscoverer,
    SubmoduleHasDefinitionDiscoverer,
)
from betty.importlib import fully_qualified_name
from betty.service_level import ServiceLevel
from betty.tests.discoverers.module_fixtures import (
    ClsDefinition,
    Definition,
    module,
)

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


class TestEntryPointDiscoverer:
    _group = "my_first_group"

    async def test___call____definition(self, mocker: MockerFixture) -> None:
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints([
                EntryPoint(
                    name="definition",
                    value=module.__name__ + ":definition",
                    group=self._group,
                ),
                EntryPoint(name="module", value=module.__name__, group=self._group),
            ]),
        )
        sut = EntryPointDiscoverer(Definition, self._group)
        discovered = list(sut(ServiceLevel()))
        assert len(discovered) == 2
        assert discovered[0] is module.definition
        assert isinstance(discovered[1], DefinitionDiscoverer)
        m_entry_points.assert_called_once_with(group=f"betty.{self._group}")

    async def test___call____cls(self, mocker: MockerFixture) -> None:
        m_entry_points = mocker.patch(
            "importlib.metadata.entry_points",
            return_value=EntryPoints([
                EntryPoint(
                    name="cls",
                    value=fully_qualified_name(module.Cls),
                    group=self._group,
                ),
                EntryPoint(name="module", value=module.__name__, group=self._group),
            ]),
        )
        sut = EntryPointDiscoverer(ClsDefinition, self._group)
        discovered = list(sut(ServiceLevel()))
        assert len(discovered) == 3
        assert discovered[0] is module.Cls.definition
        assert isinstance(discovered[1], HasDefinitionDiscoverer)
        assert isinstance(discovered[2], SubmoduleHasDefinitionDiscoverer)
        m_entry_points.assert_called_once_with(group=f"betty.{self._group}")
