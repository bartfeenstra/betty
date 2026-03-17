import ast
import builtins
import re
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
from betty.console.command import CommandDefinition
from betty.dirs import ROOT_DIRECTORY_PATH
from betty.documentation import DocumentationServer
from betty.functools import Do
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.test_utils.documentation import PluginDocumentationTestBase
from betty.test_utils.user import StaticUser


class TestDocumentationServer:
    @pytest.mark.order(0)
    async def test(self, mocker: MockerFixture, tmp_path: Path) -> None:
        mocker.patch("webbrowser.open_new_tab")
        async with DocumentationServer(tmp_path, user=StaticUser()) as server:

            def _assert_response(response: Response) -> None:
                assert response.status_code == 200
                assert "Betty" in response.content.decode("utf-8")

            await Do(requests.get, server.public_url).until(_assert_response)


class TestDocumentation:
    async def test_should_contain_console_help(self, isolated_app: App) -> None:
        async with aiofiles.open(
            ROOT_DIRECTORY_PATH / "documentation" / "usage" / "console.rst"
        ) as f:
            actual = await f.read()
        async for command in isolated_app.plugins[CommandDefinition]:
            assert command.id in actual
            assert command.label.localize(DEFAULT_LOCALIZER) in actual


class TestPluginDocumentation(PluginDocumentationTestBase):
    _module = "betty"


class TestDocstringSphinxReferences:
    async def test(self, subtests: pytest.Subtests) -> None:
        for directory_path, _, file_names in walk(str(ROOT_DIRECTORY_PATH / "betty")):
            for file_name in file_names:
                if file_name.endswith(".py"):
                    await self._assert_docstring_file(
                        Path(directory_path) / file_name, subtests
                    )

    async def _assert_docstring_file(
        self, file_path: Path, subtests: pytest.Subtests
    ) -> None:
        async with aiofiles.open(file_path, encoding="utf-8") as f:
            source = await f.read()
        module = ast.parse(source)
        for node in ast.walk(module):
            if isinstance(
                node,
                ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module,
            ):
                docstring = ast.get_docstring(node)
                if docstring is None:
                    continue
                await _assert_sphinx_references(file_path, docstring, subtests)


class TestDocumentationSphinxReferences:
    async def test(self, subtests: pytest.Subtests) -> None:
        for directory_path, _, file_names in walk(
            str(ROOT_DIRECTORY_PATH / "documentation")
        ):
            for file_name in file_names:
                if file_name.endswith(".rst"):
                    await self._assert_rst_file(
                        Path(directory_path) / file_name, subtests
                    )

    async def _assert_rst_file(
        self, file_path: Path, subtests: pytest.Subtests
    ) -> None:
        async with aiofiles.open(file_path) as f:
            documentation = await f.read()
        await _assert_sphinx_references(file_path, documentation, subtests)


def _normalize_sphinx_ref(ref: str) -> str:
    return ref.lstrip("~")


def _sphinx_refs(source: str, ref_tag: str) -> Iterator[tuple[str, str]]:
    for match in re.finditer(
        f"(:{ref_tag}:`[^`]+?<([^`]+?)>`)|(:{ref_tag}:`([^`]+?)`)", source
    ):
        if match.group(1) is None:
            yield match.group(3), _normalize_sphinx_ref(match.group(4))
        else:
            yield match.group(1), _normalize_sphinx_ref(match.group(2))


async def _assert_sphinx_references(
    file_path: Path, source: str, subtests: pytest.Subtests
) -> None:
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
                with subtests.test():
                    raise AssertionError(
                        f"Cannot import {py_ref} as mentioned by {py_ref} in {file_path}."
                    ) from error

    for doc_ref, doc_ref_target in _sphinx_refs(source, "doc"):
        doc_path = ROOT_DIRECTORY_PATH.joinpath(
            "documentation", *doc_ref_target.split("/")
        ).with_suffix(".rst")
        if not doc_path.is_file():
            with subtests.test():
                raise AssertionError(
                    f'Cannot find documentation page "{doc_ref_target}" as mentioned by {doc_ref} in {file_path}.'
                )
