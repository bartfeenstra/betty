from json import dumps
from tempfile import TemporaryFile
from typing import Any, Dict
from unittest import TestCase

from betty.config import from_file


class FromTest(TestCase):
    _MINIMAL_CONFIG_DICT = {
        'inputGrampsFilePath': '/tmp/path/to/data.xml',
        'outputDirectoryPath': '/tmp/path/to/site',
        'url': 'https://example.com',
    }

    def _writes(self, config: str):
        f = TemporaryFile(mode='r+')
        f.write(config)
        f.seek(0)
        return f

    def _write(self, config_dict: Dict[str, Any]):
        return self._writes(dumps(config_dict))

    def test_from_file_should_parse_minimal(self):
        with self._write(self._MINIMAL_CONFIG_DICT) as f:
            configuration = from_file(f)
        self.assertEquals(configuration.input_gramps_file_path, self._MINIMAL_CONFIG_DICT['inputGrampsFilePath'])
        self.assertEquals(configuration.output_directory_path, self._MINIMAL_CONFIG_DICT['outputDirectoryPath'])
        self.assertEquals(configuration.url, self._MINIMAL_CONFIG_DICT['url'])
        self.assertEquals(configuration.title, 'Betty')

    def test_from_file_should_parse_title(self):
        title = 'My first Betty site'
        config_dict = self._MINIMAL_CONFIG_DICT
        config_dict['title'] = title
        with self._write(config_dict) as f:
            configuration = from_file(f)
            self.assertEquals(configuration.title, title)

    def test_from_file_should_error_if_invalid_json(self):
        with self._writes('') as f:
            with self.assertRaises(ValueError):
                from_file(f)

    def test_from_file_should_error_if_invalid_config(self):
        config_dict = {}
        with self._write(config_dict) as f:
            with self.assertRaises(ValueError):
                from_file(f)
