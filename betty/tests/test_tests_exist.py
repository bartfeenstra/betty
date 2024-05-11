from _ast import Expr, Constant
from ast import parse, iter_child_nodes
from collections.abc import Sequence, Iterator
from configparser import ConfigParser
from glob import glob
from pathlib import Path

import aiofiles

from betty.fs import iterfiles, ROOT_DIRECTORY_PATH


class TestTestsExist:
    # These modules files are known to have no coverage, and form the baseline this
    # test operates on. This baseline MUST NOT be extended. It SHOULD decrease in
    # size as more coverage is added to Betty over time.
    _BASELINE_BETTY_MODULE_FILES = {
        "betty/__init__.py",
        "betty/_patch.py",
        "betty/app/extension/requirement.py",
        "betty/cache/_base.py",
        "betty/classtools.py",
        "betty/dispatch.py",
        "betty/error.py",
        "betty/extension/__init__.py",
        "betty/extension/nginx/docker.py",
        "betty/extension/webpack/jinja2/__init__.py",
        "betty/extension/webpack/jinja2/filter.py",
        "betty/gramps/error.py",
        "betty/gui/__init__.py",
        "betty/gui/error.py",
        "betty/gui/locale.py",
        "betty/gui/logging.py",
        "betty/gui/model.py",
        "betty/gui/serve.py",
        "betty/gui/text.py",
        "betty/gui/window.py",
        "betty/html.py",
        "betty/jinja2/__init__.py",
        "betty/jinja2/filter.py",
        "betty/jinja2/test.py",
        "betty/json/linked_data.py",
        "betty/load.py",
        "betty/path.py",
        "betty/render.py",
        "betty/serde/dump.py",
        "betty/sphinx/extension/replacements.py",
        "betty/warnings.py",
    }

    async def test(self) -> None:
        async for file_path in iterfiles(ROOT_DIRECTORY_PATH / "betty"):
            if file_path.suffix == ".py":
                await self._test_python_file(file_path)

    def _module_path_to_name(self, relative_module_path: Path) -> str:
        module_name_parts = relative_module_path.parent.parts
        if relative_module_path.name != "__init__.py":
            module_name_parts = (*module_name_parts, relative_module_path.name[:-3])
        return ".".join(module_name_parts)

    def _get_coveragerc_ignore_modules(self) -> Iterator[Path]:
        coveragerc = ConfigParser()
        coveragerc.read(ROOT_DIRECTORY_PATH / ".coveragerc")
        omit = coveragerc.get("run", "omit").split("\n")
        for omit_pattern in omit:
            for module_path_str in glob(omit_pattern, recursive=True):
                if not module_path_str.endswith(".py"):
                    continue
                module_path = Path(module_path_str)
                if not module_path.is_file():
                    continue
                yield module_path

    async def _get_ignore_module_paths(self) -> Sequence[Path]:
        return (
            *map(Path, self._BASELINE_BETTY_MODULE_FILES),
            *self._get_coveragerc_ignore_modules(),
        )

    async def _test_python_file(self, file_path: Path) -> None:
        # Skip tests.
        if ROOT_DIRECTORY_PATH / "betty" / "tests" in file_path.parents:
            return

        module_path = file_path.relative_to(ROOT_DIRECTORY_PATH)

        ignore_module_paths = await self._get_ignore_module_paths()

        expected_test_file_path = (
            ROOT_DIRECTORY_PATH
            / "betty"
            / "tests"
            / file_path.relative_to(ROOT_DIRECTORY_PATH / "betty").parent
            / f"test_{file_path.name}"
        )
        if expected_test_file_path.exists():
            for ignore_module_path in ignore_module_paths:
                if module_path == ignore_module_path:
                    raise AssertionError(
                        f"{module_path} has a matching test file at {ignore_module_path}, but was unexpectedly configured to be ignored."
                    )
            return

        if module_path in ignore_module_paths:
            return

        if await self._test_python_module_contains_docstring_only(file_path):
            return

        raise AssertionError(
            f"{module_path} does not have a matching test file. Expected {expected_test_file_path} to exist."
        )

    async def _test_python_module_contains_docstring_only(
        self, file_path: Path
    ) -> bool:
        async with aiofiles.open(file_path) as f:
            f_content = await f.read()
        f_ast = parse(f_content)
        for child in iter_child_nodes(f_ast):
            if not isinstance(child, Expr):
                return False
            if not isinstance(child.value, Constant):
                return False
        return True
