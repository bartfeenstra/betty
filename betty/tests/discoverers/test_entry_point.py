from __future__ import annotations

from importlib.metadata import EntryPoint, EntryPoints
from typing import TYPE_CHECKING

from betty.discoverers.entry_point import EntryPointDiscovery
from betty.discoverers.module import (
    ModuleClsDiscovery,
    ModuleDefinitionDiscovery,
    SubmoduleClsDiscovery,
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


class TestEntryPointDiscovery:
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
        sut = EntryPointDiscovery(Definition, self._group)
        discovered = list(sut(ServiceLevel()))
        assert len(discovered) == 2
        assert discovered[0] is module.definition
        assert isinstance(discovered[1], ModuleDefinitionDiscovery)
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
        sut = EntryPointDiscovery(ClsDefinition, self._group)
        discovered = list(sut(ServiceLevel()))
        assert len(discovered) == 3
        assert discovered[0] is module.Cls.definition
        assert isinstance(discovered[1], ModuleClsDiscovery)
        assert isinstance(discovered[2], SubmoduleClsDiscovery)
        m_entry_points.assert_called_once_with(group=f"betty.{self._group}")
