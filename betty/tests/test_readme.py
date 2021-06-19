import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty import os, subprocess


class ReadmeTest(TestCase):
    def test_readme_should_contain_cli_help(self):
        with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration = {
                'base_url': 'https://example.com',
                'output': str(working_directory_path / 'output'),
            }
            with open(working_directory_path / 'betty.json', 'w') as f:
                json.dump(configuration, f)
            with os.ChDir(working_directory_path):
                expected = subprocess.run(['betty', '--help'], universal_newlines=True).stdout
            with open('README.md') as f:
                actual = f.read()
            self.assertIn(expected, actual)
