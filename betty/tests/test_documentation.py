import json
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import pytest
import requests
from aiofiles.tempfile import TemporaryDirectory
from betty.cli import _BettyCommands
from betty.cli.commands import COMMAND_REPOSITORY
from betty.documentation import DocumentationServer
from betty.fs import ROOT_DIRECTORY_PATH
from betty.functools import Do
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project import ProjectConfiguration
from betty.serde.format import Format, Json, Yaml
from betty.test_utils.cli import run
from pytest_mock import MockerFixture
from requests import Response

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
    async def _get_help(self, command: str | None = None) -> str:
        _BettyCommands.terminal_width = 80
        args: tuple[str, ...] = ("--help",)
        if command is not None:
            args = (command, *args)
        expected = (await run(*args)).stdout.strip()
        if sys.platform.startswith("win32"):
            expected = expected.replace("\r\n", "\n")
        return "\n".join(
            (f"    {line}" if line.strip() else "" for line in expected.split("\n"))
        )

    async def test_should_contain_cli_help(self) -> None:
        async with TemporaryDirectory() as working_directory_path_str:
            working_directory_path = Path(working_directory_path_str)
            configuration: DumpMapping[Dump] = {
                "url": "https://example.com",
                "extensions": {
                    "nginx": {},
                },
            }
            async with aiofiles.open(working_directory_path / "betty.json", "w") as f:
                await f.write(json.dumps(configuration))
            async with aiofiles.open(
                ROOT_DIRECTORY_PATH / "documentation" / "usage" / "cli.rst"
            ) as f:
                actual = await f.read()
            assert await self._get_help() in actual
            async for command in COMMAND_REPOSITORY:
                if command.plugin_id() in (
                    "dev-new-translation",
                    "dev-update-translations",
                ):
                    continue
                assert await self._get_help(command.plugin_id()) in actual

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
