from collections.abc import Sequence
from unittest.mock import AsyncMock

from typing_extensions import override

from betty.data import DataDefinition
from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Key
from betty.service.level.universal import universe
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestAggregateDefinition:
    async def test_hydrate(self) -> None:
        m_element = AsyncMock(spec=DataDefinition)

        class _Sut(AggregateDefinition[dict[str, object], Key]):
            def __init__(self):
                super().__init__(cls=dict[str, object], label=DUMMY_LOCALIZABLE)

            @override
            def elements(
                self, data: dict[str, object]
            ) -> Sequence[tuple[Key, DataDefinition]]:
                return [
                    (
                        Key("key"),
                        m_element,
                    )
                ]

        element_data = object()
        sut = _Sut()
        await sut.hydrate({"key": element_data}, universe)
        m_element.hydrate.assert_awaited_once_with(element_data, universe)
