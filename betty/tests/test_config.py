from json import dump
from tempfile import TemporaryFile
from unittest import TestCase

from betty.config import from_file


class FromTest(TestCase):
    def test_from_file_should_parse(self):
        input_gramps_file_path = '/tmp/path/to/data.xml'
        output_directory_path = '/tmp/path/to/site'
        config_dict = {
            'inputGrampsFilePath': input_gramps_file_path,
            'outputDirectoryPath': output_directory_path,
        }
        with TemporaryFile(mode='r+') as f:
            dump(config_dict, f)
            f.seek(0)
            configuration = from_file(f)
        self.assertEquals(configuration.input_gramps_file_path, input_gramps_file_path)
        self.assertEquals(configuration.output_directory_path, output_directory_path)

    def test_from_file_should_error_if_invalid_json(self):
        with TemporaryFile(mode='r+') as f:
            with self.assertRaises(ValueError):
                from_file(f)

    def test_from_file_should_error_if_invalid_config(self):
        config_dict = {}
        with TemporaryFile(mode='r+') as f:
            dump(config_dict, f)
            f.seek(0)
            with self.assertRaises(ValueError):
                from_file(f)
