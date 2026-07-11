import pytest
from jsonschema import ValidationError

from betty.json_schema import validate
from betty.json_schemas.plugin_id import new_plugin_id_schema
from betty.test_utils.plugin import DummyPluginDefinition, DummyPluginOne


def test_new_plugin_id_schema() -> None:
    sut = new_plugin_id_schema(
        DummyPluginDefinition.type(),
        [DummyPluginOne.plugin()],
    )
    validate(sut, "dummy-plugin-one")
    with pytest.raises(ValidationError):
        validate(sut, "dummy-plugin-two")
