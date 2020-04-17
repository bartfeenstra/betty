import json
from os import path
from subprocess import check_output
from tempfile import TemporaryDirectory
from unittest import TestCase

from betty import os


class ReadmeTest(TestCase):
    def test_readme_should_contain_cli_help(self):
        with TemporaryDirectory() as betty_site_path:
            configuration = {
                'base_url': 'https://example.com',
                'output': path.join(betty_site_path, 'output'),
            }
            with open(path.join(betty_site_path, 'betty.json'), 'w') as f:
                json.dump(configuration, f)
            with os.chdir(betty_site_path):
                expected = check_output(['betty', '--help'])
            with open('README.md') as f:
                actual = f.read().encode()
            self.assertIn(expected, actual)
