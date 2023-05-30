import json
import subprocess as stdsubprocess
import sys
from asyncio import StreamReader

from betty import os, subprocess
from betty.tempfile import TemporaryDirectory


class TestReadme:
    async def test_readme_should_contain_cli_help(self):
        with TemporaryDirectory() as working_directory_path:
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
