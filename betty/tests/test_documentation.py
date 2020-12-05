import html
import json
from gettext import NullTranslations
from os import path
from tempfile import TemporaryDirectory
from textwrap import indent
from unittest import TestCase

from betty import os, subprocess
from betty.about import copyright_message
from betty.documentation import build
from betty.locale import Translations


class BuildTest(TestCase):
    def test(self) -> None:
        with TemporaryDirectory() as output_directory_path:
            build(output_directory_path)
            with open(path.join(output_directory_path, 'index.html')) as f:
                documentation_index = f.read()
            self.assertIn('Betty', documentation_index)
            with Translations(NullTranslations()):
                self.assertIn(html.escape(copyright_message()), documentation_index)


class CliHelpTest(TestCase):
    def test_cli_should_contain_cli_help(self) -> None:
        with TemporaryDirectory() as working_directory_path:
            configuration = {
                'base_url': 'https://example.com',
                'output': path.join(working_directory_path, 'output'),
            }
            with open(path.join(working_directory_path, 'betty.json'), 'w') as f:
                json.dump(configuration, f)
            with os.ChDir(working_directory_path):
                help_result = subprocess.run(['betty', '--help'], universal_newlines=True)
                expected = indent(help_result.stdout, '    ')
            with open(path.join('documentation', 'cli.rst')) as f:
                actual = f.read()
            self.assertIn(expected, actual)
