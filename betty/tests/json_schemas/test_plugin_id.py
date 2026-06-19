from betty.json_schemas.plugin_id import PluginIdSchema
from betty.test_utils.plugin import (
    DummyPluginDefinition,
    DummyPluginOne,
    DummyPluginThree,
    DummyPluginTwo,
)


class TestPluginIdSchema:
    def test(self) -> None:
        sut = PluginIdSchema(
            DummyPluginDefinition.type(),
            [
                DummyPluginOne.plugin(),
                DummyPluginTwo.plugin(),
                DummyPluginThree.plugin(),
            ],
        )
        assert sut.schema["enum"] == [
            "dummy-plugin-one",
            "dummy-plugin-two",
            "dummy-plugin-three",
        ]
