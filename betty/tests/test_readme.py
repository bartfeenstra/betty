import json
import sys
from pathlib import Path
import subprocess as stdsubprocess
from tempfile import TemporaryDirectory

from betty import os, subprocess
from betty.asyncio import sync
from betty.tests import TestCase


class ReadmeTest(TestCase):
    @sync
    async def test_readme_should_contain_cli_help(self):
        with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration = {
                'base_url': 'https://example.com',
            }
            with open(working_directory_path / 'betty.json', 'w') as f:
                json.dump(configuration, f)
            with os.ChDir(working_directory_path):
                process = await subprocess.run_exec(['betty', '--help'], stdout=stdsubprocess.PIPE)
            expected = (await process.stdout.read()).decode()
            if sys.platform.startswith('win32'):
                expected = expected.replace('\r\n', '\n')
            with open('README.md') as f:
                actual = f.read()
            self.assertIn(expected, actual)
