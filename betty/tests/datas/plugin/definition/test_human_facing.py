from betty.datas.plugin.definition.human_facing import (
    CountableHumanFacingPluginDefinitionData,
    HumanFacingPluginDefinitionData,
)
from betty.test_utils.locale.localizable import (
    DUMMY_COUNTABLE_LOCALIZABLE,
    DUMMY_LOCALIZABLE,
)
from betty.tests.datas.plugin.test_definition import _DummyPluginDefinitionData


class TestHumanFacingPluginDefinitionData:
    class _Sut(HumanFacingPluginDefinitionData, _DummyPluginDefinitionData):
        pass

    def test_label(self) -> None:
        label = DUMMY_LOCALIZABLE
        sut = self._Sut(id="hello-world", label=label)
        assert sut.label is label

    def test_description(self) -> None:
        description = DUMMY_LOCALIZABLE
        sut = self._Sut(id="hello-world", label="-", description=description)
        assert sut.description is description


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
