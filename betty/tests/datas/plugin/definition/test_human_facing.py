from betty.datas.plugin.definition.human_facing import (
    CountableHumanFacingPluginDefinitionData,
    HumanFacingPluginDefinitionData,
)
from betty.test_utils.locale.localizable import dummy_countable_localizable
from betty.tests.datas.plugin.test_definition import _DummyPluginDefinitionData


class TestHumanFacingPluginDefinitionData:
    class _Sut(HumanFacingPluginDefinitionData, _DummyPluginDefinitionData):
        pass

    def test_label(self) -> None:
        label = "Hello, world!"
        sut = self._Sut(id="hello-world", label=label)
        assert sut.label == label

    def test_description(self) -> None:
        description = "Hello, world!"
        sut = self._Sut(id="hello-world", label="-", description=description)
        assert sut.description == description


class TestCountableHumanFacingPluginDefinitionData:
    class _Sut(
        CountableHumanFacingPluginDefinitionData,
        _DummyPluginDefinitionData,
    ):
        pass

    def test_label_plural(self) -> None:
        label_plural = "Hello, worlds!"
        sut = self._Sut(
            id="-dummy",
            label="-",
            label_plural=label_plural,
            label_countable=dummy_countable_localizable,
        )
        assert sut.label_plural == label_plural

    def test_label_countable(self) -> None:
        label_countable = dummy_countable_localizable
        sut = self._Sut(
            id="-dummy", label="-", label_plural="-", label_countable=label_countable
        )
        assert sut.label_countable == label_countable
