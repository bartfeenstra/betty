import json
import re
import sys
from asyncio import StreamReader
from contextlib import chdir
from pathlib import Path

import aiofiles
import pytest
from aiofiles.tempfile import TemporaryDirectory

from betty.fs import ROOT_DIRECTORY_PATH
from betty.project import ProjectConfiguration
from betty.serde.format import Format, Json, Yaml
from betty.subprocess import run_process


class TestDocumentation:
    async def test_should_contain_cli_help(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration = {
                'base_url': 'https://example.com',
            }
            async with aiofiles.open(working_directory_path / 'betty.json', 'w') as f:
                await f.write(json.dumps(configuration))
            with chdir(working_directory_path):
                process = await run_process(['betty', '--help'])
            stdout = process.stdout
            assert isinstance(stdout, StreamReader)
            expected = (await stdout.read()).decode().strip()
            if sys.platform.startswith('win32'):
                expected = expected.replace('\r\n', '\n')
            expected = '\n'.join(map(lambda line: f'    {line}' if line.strip() else '', expected.split('\n')))
            async with aiofiles.open(ROOT_DIRECTORY_PATH / 'documentation' / 'usage' / 'cli.rst') as f:
                actual = await f.read()
            assert expected in actual

    @pytest.mark.parametrize('language, format', [
        ('yaml', Yaml()),
        ('json', Json()),
    ])
    async def test_should_contain_valid_configuration(self, language: str, format: Format) -> None:
        async with aiofiles.open(ROOT_DIRECTORY_PATH / 'documentation' / 'usage' / 'project' / 'configuration.rst') as f:
            actual = await f.read()
        match = re.search(rf'^      \.\. code-block:: {language}\n\n((.|\n)+?)\n\n', actual, re.MULTILINE)
        assert match is not None
        dump = match[1]
        assert dump is not None
        configuration = ProjectConfiguration()
        configuration.load(format.load(dump))
