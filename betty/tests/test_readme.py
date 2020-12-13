import json
from os import path
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty import os, subprocess


class ReadmeTest(TestCase):
    def test_readme_should_contain_cli_help(self):
        with TemporaryDirectory() as betty_site_path:
            configuration = {
                'base_url': 'https://example.com',
                'output': path.join(betty_site_path, 'output'),
            }
            with open(path.join(betty_site_path, 'betty.json'), 'w') as f:
                json.dump(configuration, f)
            with os.ChDir(betty_site_path):
                expected = subprocess.run(['betty', '--help'], universal_newlines=True).stdout
            with open('README.md') as f:
                actual = f.read()
            self.assertIn(expected, actual)
