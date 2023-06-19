import json
import re
import subprocess as stdsubprocess
import sys
from asyncio import StreamReader

import yaml

from betty import os, subprocess
from betty.project import ProjectConfiguration
from betty.tempfile import TemporaryDirectory


class TestReadme:
    async def test_readme_should_contain_cli_help(self) -> None:
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

    async def test_readme_should_contain_valid_configuration(self) -> None:
        with open('README.md') as f:
            readme = f.read()
        match = re.search(r'^```yaml\nbase_url((.|\n)+?)```$', readme, re.MULTILINE)
        assert match is not None
        raw_dump = match[0][7:-3]
        configuration = ProjectConfiguration()
        configuration.load(yaml.safe_load(raw_dump))
