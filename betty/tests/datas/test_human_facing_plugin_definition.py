from betty.datas.human_facing_plugin_definition import HumanFacingPluginDefinitionData
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE
from betty.tests.datas.test_plugin_definition import _DummyPluginDefinitionData


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
