from subprocess import check_output
from unittest import TestCase


class ReadmeTest(TestCase):
    def test_readme_should_contain_cli_help(self):
        expected = check_output(['betty', '--help'])
        with open('README.md') as f:
            actual = f.read().encode()
        self.assertIn(expected, actual)
