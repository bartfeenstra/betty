import pytest

from betty.app import App
from betty.config import ConfigurationFormatError, DumpedConfigurationImport
from betty.config.format import Yaml, Json


class TestJson:
    def test_load_with_invalid_json(self) -> None:
        sut = Json()
        dumped_json = '@'
        with App():
            with pytest.raises(ConfigurationFormatError):
                sut.load(dumped_json)

    def test_load_with_valid_json(self) -> None:
        sut = Json()
        dumped_json = '{"hello": [123, "World!"]}'
        dumped_configuration = sut.load(dumped_json)
        expected = {
            'hello': [123, 'World!']
        }
        assert expected == dumped_configuration

    def test_dump(self) -> None:
        dumped_configuration: DumpedConfigurationImport = {
            'hello': [123, 'World!']
        }
        sut = Json()
        dumped_json = sut.dump(dumped_configuration)
        assert '{"hello": [123, "World!"]}' == dumped_json


class TestYaml:
    def test_load_with_invalid_yaml(self) -> None:
        sut = Yaml()
        dumped_yaml = '@'
        with App():
            with pytest.raises(ConfigurationFormatError):
                sut.load(dumped_yaml)

    def test_load_with_valid_yaml(self) -> None:
        sut = Yaml()
        dumped_yaml = 'hello:\n- 123\n- World!\n'
        dumped_configuration = sut.load(dumped_yaml)
        expected = {
            'hello': [123, 'World!']
        }
        assert expected == dumped_configuration

    def test_dump(self) -> None:
        dumped_configuration: DumpedConfigurationImport = {
            'hello': [123, 'World!']
        }
        sut = Yaml()
        dumped_yaml = sut.dump(dumped_configuration)
        assert 'hello:\n- 123\n- World!\n' == dumped_yaml
