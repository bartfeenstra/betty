import ast
import builtins
import re
import sys
from collections.abc import Iterator
from os import walk
from pathlib import Path

import aiofiles
import pytest
import requests
from pytest_mock import MockerFixture
from requests import Response
from sphinx.errors import ExtensionError
from sphinx.util import import_object

from betty.app import App
from betty.cli import _BettyCommands
from betty.cli.commands import COMMAND_REPOSITORY
from betty.documentation import DocumentationServer
from betty.fs import ROOT_DIRECTORY_PATH
from betty.functools import Do
from betty.jinja2.filter import filters
from betty.jinja2.test import tests
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.project.config import ProjectConfiguration
from betty.serde.format import Format
from betty.serde.format.formats import Json, Yaml
from betty.test_utils.cli import run


class TestDocumentationServer:
    async def test(self, mocker: MockerFixture, tmp_path: Path) -> None:
        mocker.patch("webbrowser.open_new_tab")
        async with DocumentationServer(tmp_path, localizer=DEFAULT_LOCALIZER) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty Documentation" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)


class TestDocumentation:
    async def _get_help(self, app: App, command: str | None = None) -> str:
        _BettyCommands.terminal_width = 80
        args: tuple[str, ...] = ("--help",)
        if command is not None:
            args = (command, *args)
        expected = (await run(app, *args)).stdout.strip()
        if sys.platform.startswith("win32"):
            expected = expected.replace("\r\n", "\n")
        return "\n".join(
            (f"    {line}" if line.strip() else "" for line in expected.split("\n"))
        )

    async def test_should_contain_cli_help(self, new_temporary_app: App) -> None:
        async with aiofiles.open(
            ROOT_DIRECTORY_PATH / "documentation" / "usage" / "cli.rst"
        ) as f:
            actual = await f.read()
        assert await self._get_help(new_temporary_app) in actual
        async for command in COMMAND_REPOSITORY:
            if command.plugin_id() in (
                "dev-new-translation",
                "dev-update-translations",
            ):
                continue
            assert (
                await self._get_help(new_temporary_app, command.plugin_id()) in actual
            )

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
        configuration = await ProjectConfiguration.new(tmp_path / "betty.json")
        configuration.load(serde_format.load(dump))

    async def test_should_contain_builtin_jinja2_filters(self) -> None:
        with open(
            ROOT_DIRECTORY_PATH
            / "documentation"
            / "usage"
            / "templating"
            / "filters.rst"
        ) as f:
            documentation = f.read()
        for filter_name in await filters():
            assert f":`{filter_name} <" in documentation

    async def test_should_contain_builtin_jinja2_tests(self) -> None:
        with open(
            ROOT_DIRECTORY_PATH / "documentation" / "usage" / "templating" / "tests.rst"
        ) as f:
            documentation = f.read()
        for test_name in await tests():
            assert f":`{test_name} <" in documentation


class TestDocstringSphinxReferences:
    async def test(self) -> None:
        for directory_path, _, file_names in walk(str(ROOT_DIRECTORY_PATH / "betty")):
            for file_name in file_names:
                if file_name.endswith(".py"):
                    await self._assert_docstring_file(Path(directory_path) / file_name)

    async def _assert_docstring_file(self, file_path: Path) -> None:
        async with aiofiles.open(file_path, encoding="utf-8") as f:
            source = await f.read()
        module = ast.parse(source)
        for node in ast.walk(module):
            if isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Module,
                ),
            ):
                docstring = ast.get_docstring(node)
                if docstring is None:
                    continue
                await _assert_sphinx_references(file_path, docstring)


class TestDocumentationSphinxReferences:
    async def test(self) -> None:
        for directory_path, _, file_names in walk(
            str(ROOT_DIRECTORY_PATH / "documentation")
        ):
            for file_name in file_names:
                if file_name.endswith(".rst"):
                    await self._assert_rst_file(Path(directory_path) / file_name)

    async def _assert_rst_file(self, file_path: Path) -> None:
        async with aiofiles.open(file_path) as f:
            documentation = await f.read()
        await _assert_sphinx_references(file_path, documentation)


def _sphinx_refs(source: str, ref_tag: str) -> Iterator[tuple[str, str]]:
    for match in re.finditer(
        f"(:{ref_tag}:`[^`]+?<([^`]+?)>`)|(:{ref_tag}:`([^`]+?)`)", source
    ):
        if match.group(1) is None:
            yield match.group(3), match.group(4)  # type: ignore[misc]
        else:
            yield match.group(1), match.group(2)  # type: ignore[misc]


async def _assert_sphinx_references(file_path: Path, source: str) -> None:
    for ref_tag in (
        "mod",
        "func",
        "data",
        "const",
        "class",
        "meth",
        "attr",
        "type",
        "exc",
        "obj",
    ):
        for py_ref, py_ref_target in _sphinx_refs(source, ref_tag):
            if py_ref_target in builtins.__dict__:
                return
            if (
                "." in py_ref_target
                and py_ref_target.split(".")[0] in builtins.__dict__
            ):
                return
            try:
                import_object(py_ref_target)
            except ExtensionError as error:
                raise AssertionError(
                    f"Cannot import {py_ref} as mentioned by {py_ref} in {file_path}."
                ) from error

    for doc_ref, doc_ref_target in _sphinx_refs(source, "doc"):
        doc_path = ROOT_DIRECTORY_PATH.joinpath(
            "documentation", *doc_ref_target.split("/")
        ).with_suffix(".rst")
        if not doc_path.is_file():
            raise AssertionError(
                f'Cannot find documentation page "{doc_ref_target}" as mentioned by {doc_ref} in {file_path}.'
            )
