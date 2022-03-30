import json
from tempfile import NamedTemporaryFile
from typing import Any, Dict

from betty.config import from_json, from_yaml, from_file, Configuration, ConfigurationError
from betty.tests import TestCase


class FromJsonTest(TestCase):
    def test_should_error_if_invalid_json(self) -> None:
        with self.assertRaises(ConfigurationError):
            from_json('')


class FromYamlTest(TestCase):
    def test_should_error_if_invalid_yaml(self) -> None:
        with self.assertRaises(ConfigurationError):
            from_yaml('"foo')


class FromFileTest(TestCase):
    def _writes(self, config: str, extension: str) -> object:
        f = NamedTemporaryFile(mode='r+', suffix='.' + extension)
        f.write(config)
        f.seek(0)
        return f

    def _write(self, dumped_configuration: Dict[str, Any]) -> object:
        return self._writes(json.dumps(dumped_configuration), 'json')

    def test_should_error_unknown_format(self) -> None:
        with self._writes('', 'abc') as f:
            with self.assertRaises(ConfigurationError):
                from_file(f, Configuration())
