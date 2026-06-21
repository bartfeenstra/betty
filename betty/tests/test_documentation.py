import ast
import builtins
import re
from collections.abc import Iterator
from pathlib import Path

import pytest
from sphinx.errors import ExtensionError
from sphinx.util import import_object

from betty.app import App
from betty.console.command import CommandDefinition
from betty.dirs import root_directory
from betty.localizer import default_localizer
from betty.test_utils.documentation import PluginDocumentationTestBase


class TestDocumentation:
    async def test_should_contain_console_help(self, isolated_app: App) -> None:
        with open(
            root_directory / "documentation" / "usage" / "console.rst", encoding="utf-8"
        ) as f:
            actual = f.read()
        async for command in isolated_app.plugins[CommandDefinition]:
            assert command.id in actual
            assert command.label.localize(default_localizer) in actual


class TestPluginDocumentation(PluginDocumentationTestBase):
    _module = "betty"


class TestDocstringSphinxReferences:
    async def test(self, subtests: pytest.Subtests) -> None:
        for directory, _, file_names in (root_directory / "betty").walk():
            for file_name in file_names:
                if file_name.endswith(".py"):
                    await self._assert_docstring_file(directory / file_name, subtests)

    async def _assert_docstring_file(
        self, file: Path, subtests: pytest.Subtests
    ) -> None:
        with open(file, encoding="utf-8") as f:
            source = f.read()
        module = ast.parse(source)
        for node in ast.walk(module):
            if isinstance(
                node,
                ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module,
            ):
                docstring = ast.get_docstring(node)
                if docstring is None:
                    continue
                await _assert_sphinx_references(file, docstring, subtests)


class TestDocumentationSphinxReferences:
    async def test(self, subtests: pytest.Subtests) -> None:
        for directory, _, file_names in (root_directory / "documentation").walk():
            for file_name in file_names:
                if file_name.endswith(".rst"):
                    await self._assert_rst_file(directory / file_name, subtests)

    async def _assert_rst_file(self, file: Path, subtests: pytest.Subtests) -> None:
        with open(file, encoding="utf-8") as f:
            documentation = f.read()
        await _assert_sphinx_references(file, documentation, subtests)


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
    file: Path, source: str, subtests: pytest.Subtests
) -> None:
    for ref_tag in (
        "mod",
        "func",
        "data",
        "const",
        "class",
        "meth",
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
                        f"Cannot import {py_ref} as mentioned by {py_ref} in {file}."
                    ) from error

    for doc_ref, doc_ref_target in _sphinx_refs(source, "doc"):
        doc_path = root_directory.joinpath(
            "documentation", *doc_ref_target.split("/")
        ).with_suffix(".rst")
        if not doc_path.is_file():
            with subtests.test():
                raise AssertionError(
                    f'Cannot find documentation page "{doc_ref_target}" as mentioned by {doc_ref} in {file}.'
                )
