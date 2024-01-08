import json
import re
import subprocess as stdsubprocess
import sys
from asyncio import StreamReader
from pathlib import Path

import aiofiles
import yaml
from aiofiles.tempfile import TemporaryDirectory

from betty import subprocess
from betty.fs import ROOT_DIRECTORY_PATH
from betty.os import ChDir
from betty.project import ProjectConfiguration


class TestDocumentation:
    async def test_should_contain_cli_help(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration = {
                'base_url': 'https://example.com',
            }
            async with aiofiles.open(working_directory_path / 'betty.json', 'w') as f:
                await f.write(json.dumps(configuration))
            async with ChDir(working_directory_path):
                process = await subprocess.run_exec(['betty', '--help'], stdout=stdsubprocess.PIPE)
            stdout = process.stdout
            assert isinstance(stdout, StreamReader)
            expected = (await stdout.read()).decode().strip()
            if sys.platform.startswith('win32'):
                expected = expected.replace('\r\n', '\n')
            expected = '\n'.join(map(lambda line: f'    {line}' if line.strip() else '', expected.split('\n')))
            async with aiofiles.open(ROOT_DIRECTORY_PATH / 'documentation' / 'usage' / 'cli.rst') as f:
                actual = await f.read()
            assert expected in actual

    async def test_should_contain_valid_configuration(self) -> None:
        async with aiofiles.open(ROOT_DIRECTORY_PATH / 'documentation' / 'usage' / 'project' / 'configuration.rst') as f:
            actual = await f.read()
        match = re.search(r'^\.\. code-block:: yaml\n\n    base_url((.|\n)+?)\n\n', actual, re.MULTILINE)
        assert match is not None
        raw_dump = match[0][22:-2]
        configuration = ProjectConfiguration()
        configuration.load(yaml.safe_load(raw_dump))
