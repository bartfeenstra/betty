from betty.datas.countable_human_facing_plugin_definition import (
    CountableHumanFacingPluginDefinitionData,
)
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.tests.datas.test_plugin_definition import _DummyPluginDefinitionData


class TestCountableHumanFacingPluginDefinitionData:
    class _Sut(
        CountableHumanFacingPluginDefinitionData,
        _DummyPluginDefinitionData,
    ):
        pass

    def test_label_plural(self) -> None:
        label_plural = DUMMY_LOCALIZABLE
        sut = self._Sut(
            id="-dummy",
            label="-",
            label_plural=label_plural,
            label_countable=DUMMY_COUNTABLE_LOCALIZABLE,
        )
        assert sut.label_plural is label_plural

    def test_label_countable(self) -> None:
        label_countable = DUMMY_COUNTABLE_LOCALIZABLE
        sut = self._Sut(
            id="-dummy", label="-", label_plural="-", label_countable=label_countable
        )
        assert sut.label_countable is label_countable
