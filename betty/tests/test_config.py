from tempfile import NamedTemporaryFile

import pytest

from betty.app import App
from betty.config import _from_json, _from_yaml, ConfigurationError, FileBasedConfiguration


class TestFromJson:
    def test_should_error_if_invalid_json(self) -> None:
        with App():
            with pytest.raises(ConfigurationError):
                _from_json('')


class TestFromYaml:
    def test_should_error_if_invalid_yaml(self) -> None:
        with App():
            with pytest.raises(ConfigurationError):
                _from_yaml('"foo')


class TestFileBasedConfiguration:
    def test_configuration_file_path_should_error_unknown_format(self) -> None:
        configuration = FileBasedConfiguration()
        with NamedTemporaryFile(mode='r+', suffix='.abc') as f:
            with pytest.raises(ConfigurationError):
                configuration.configuration_file_path = f.name
