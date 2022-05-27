import json
import subprocess as stdsubprocess
import sys
from asyncio import StreamReader
from pathlib import Path
from tempfile import TemporaryDirectory

from betty import os, subprocess


class TestReadme:
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
            stdout = process.stdout
            assert isinstance(stdout, StreamReader)
            expected = (await stdout.read()).decode()
            if sys.platform.startswith('win32'):
                expected = expected.replace('\r\n', '\n')
            with open('README.md') as f:
                actual = f.read()
            assert expected in actual
