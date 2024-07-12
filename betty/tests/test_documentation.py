import json
import re
import sys
from asyncio import StreamReader
from contextlib import chdir
from pathlib import Path

import aiofiles
import pytest
import requests
from aiofiles.tempfile import TemporaryDirectory
from pytest_mock import MockerFixture
from requests import Response

from betty.documentation import DocumentationServer
from betty.fs import ROOT_DIRECTORY_PATH
from betty.functools import Do
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import ProjectConfiguration
from betty.serde.format import Format, Json, Yaml
from betty.subprocess import run_process
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from betty.serde.dump import DumpMapping, Dump


class TestDocumentationServer:
    async def test(self, mocker: MockerFixture, tmp_path: Path) -> None:
        mocker.patch("webbrowser.open_new_tab")
        async with DocumentationServer(tmp_path, localizer=DEFAULT_LOCALIZER) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty Documentation" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)


class TestDocumentation:
    async def test_should_contain_cli_help(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration: DumpMapping[Dump] = {
                "base_url": "https://example.com",
                "extensions": {
                    "nginx": {},
                },
            }
            async with aiofiles.open(working_directory_path / "betty.json", "w") as f:
                await f.write(json.dumps(configuration))
            with chdir(working_directory_path):
                process = await run_process(["betty", "--help"])
            stdout = process.stdout
            assert isinstance(stdout, StreamReader)
            expected = (await stdout.read()).decode().strip()
            if sys.platform.startswith("win32"):
                expected = expected.replace("\r\n", "\n")
            expected = "\n".join(
                (f"    {line}" if line.strip() else "" for line in expected.split("\n"))
            )
            async with aiofiles.open(
                ROOT_DIRECTORY_PATH / "documentation" / "usage" / "cli.rst"
            ) as f:
                actual = await f.read()
            assert expected in actual

    @pytest.mark.parametrize(
        ("language", "serde_format"),
        [
            ("yaml", Yaml()),
            ("json", Json()),
        ],
    )
    async def test_should_contain_valid_configuration(
        self, language: str, serde_format: Format, tmp_path: Path
    ) -> None:
        async with aiofiles.open(
            ROOT_DIRECTORY_PATH
            / "documentation"
            / "usage"
            / "project"
            / "configuration.rst"
        ) as f:
            actual = await f.read()
        match = re.search(
            rf"^      \.\. code-block:: {language}\n\n((.|\n)+?)\n\n",
            actual,
            re.MULTILINE,
        )
        assert match is not None
        dump = match[1]
        assert dump is not None
        configuration = ProjectConfiguration(tmp_path / "betty.json")
        configuration.load(serde_format.load(dump))
