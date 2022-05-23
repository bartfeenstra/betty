from tempfile import NamedTemporaryFile

from betty.app import App
from betty.config import _from_json, _from_yaml, ConfigurationError, FileBasedConfiguration
from betty.tests import TestCase


class FromJsonTest(TestCase):
    def test_should_error_if_invalid_json(self) -> None:
        with App():
            with self.assertRaises(ConfigurationError):
                _from_json('')


class FromYamlTest(TestCase):
    def test_should_error_if_invalid_yaml(self) -> None:
        with App():
            with self.assertRaises(ConfigurationError):
                _from_yaml('"foo')


class FileBasedConfigurationTest(TestCase):
    def test_configuration_file_path_should_error_unknown_format(self) -> None:
        configuration = FileBasedConfiguration()
        with NamedTemporaryFile(mode='r+', suffix='.abc') as f:
            with self.assertRaises(ConfigurationError):
                configuration.configuration_file_path = f.name
