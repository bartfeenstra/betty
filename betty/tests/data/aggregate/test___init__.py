from collections.abc import Sequence
from typing import Any

import pytest
from typing_extensions import override

from betty.data import DataDefinition
from betty.data.aggregate import AggregateDefinition
from betty.data.indicator.selector import Key
from betty.exception import HumanFacingException
from betty.service.level import ServiceLevel
from betty.service.level.universal import universe
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


class TestAggregateDefinition:
    async def test_hydrate(self) -> None:
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
                        DataDefinition(cls=object, label=DUMMY_LOCALIZABLE),
                    )
                ]

            @override
            async def _hydrate_element(
                self, services: ServiceLevel, data: Any, selector: Key, /
            ) -> None:
                raise HumanFacingException("Uh-oh!")

        element_data = object()
        sut = _Sut()
        with pytest.raises(HumanFacingException) as exc_info:
            await sut.hydrate(universe, {"key": element_data})
        assert exc_info.value.indicators == [Key("key")]
