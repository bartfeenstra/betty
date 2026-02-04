from collections.abc import Sequence

import pytest
from typing_extensions import override

from betty.data import DataDefinition
from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Key
from betty.exception import HumanFacingException
from betty.service.hydrate import Hydratable
from betty.service.level import ServiceLevel, universe
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class _AggregateDefinitionTestData(Hydratable):
    @override
    async def hydrate(self, services: ServiceLevel, /) -> None:
        raise HumanFacingException("Uh-oh!")


class TestAggregateDefinition:
    async def test_hydrate(self) -> None:
        class _Sut(AggregateDefinition[dict[str, _AggregateDefinitionTestData], Key]):
            def __init__(self):
                super().__init__(cls=dict, label=DUMMY_LOCALIZABLE)

            @override
            def elements(
                self, data: dict[str, _AggregateDefinitionTestData]
            ) -> Sequence[tuple[Key, DataDefinition]]:
                return [
                    (
                        Key("key"),
                        DataDefinition(
                            cls=_AggregateDefinitionTestData, label=DUMMY_LOCALIZABLE
                        ),
                    )
                ]

        sut = _Sut()
        with pytest.raises(HumanFacingException) as exc_info:
            await sut.hydrate(universe, {"key": _AggregateDefinitionTestData()})
        assert exc_info.value.indicators == [Key("key")]
