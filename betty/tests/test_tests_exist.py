from _ast import Expr, Constant
from ast import parse, iter_child_nodes
from pathlib import Path

import aiofiles

from betty.fs import iterfiles, ROOT_DIRECTORY_PATH


class TestTestsExist:
    # These modules are known to have no coverage, and form the baseline this test
    # operates on. This baseline MUST NOT be extended. It SHOULD decrease in size
    # as more coverage is added to Betty over time.
    _BASELINE_MODULES = {
        "betty.__init__",
        "betty._package.__init__",
        "betty._package.pyinstaller.__init__",
        "betty._package.pyinstaller.hooks.__init__",
        "betty._package.pyinstaller.hooks.hook-betty",
        "betty._package.pyinstaller.main",
        "betty._patch",
        "betty._resizeimage",
        "betty.app.extension.requirement",
        "betty.cache._base",
        "betty.classtools",
        "betty.dispatch",
        "betty.error",
        "betty.extension.__init__",
        "betty.extension.nginx.docker",
        "betty.extension.webpack.jinja2.__init__",
        "betty.extension.webpack.jinja2.filter",
        "betty.gramps.error",
        "betty.gui.__init__",
        "betty.gui.error",
        "betty.gui.locale",
        "betty.gui.logging",
        "betty.gui.model",
        "betty.gui.serve",
        "betty.gui.text",
        "betty.gui.window",
        "betty.html",
        "betty.jinja2.__init__",
        "betty.jinja2.filter",
        "betty.jinja2.test",
        "betty.json.linked_data",
        "betty.load",
        "betty.model.event_type",
        "betty.path",
        "betty.render",
        "betty.serde.dump",
        "betty.sphinx.extension.replacements",
        "betty.warnings",
    }

    async def test(self) -> None:
        async for file_path in iterfiles(ROOT_DIRECTORY_PATH / "betty"):
            if file_path.suffix == ".py":
                await self._test_python_file(file_path)

    async def _test_python_file(self, file_path: Path) -> None:
        # Skip tests.
        if ROOT_DIRECTORY_PATH / "betty" / "tests" in file_path.parents:
            return

        module_name = ".".join(
            (
                *file_path.relative_to(ROOT_DIRECTORY_PATH).parent.parts,
                file_path.stem,
            )
        )

        expected_test_file_path = (
            ROOT_DIRECTORY_PATH
            / "betty"
            / "tests"
            / file_path.relative_to(ROOT_DIRECTORY_PATH / "betty").parent
            / f"test_{file_path.name}"
        )
        if expected_test_file_path.exists():
            for baseline_module in self._BASELINE_MODULES:
                if module_name == baseline_module or module_name.startswith(
                    f"{baseline_module}."
                ):
                    raise AssertionError(
                        f"Module {module_name} has a matching test file, but unexpectedly matches the baseline module {baseline_module}."
                    )
            return

        if module_name in self._BASELINE_MODULES:
            return

        if await self._test_python_module_contains_docstring_only(file_path):
            return

        raise AssertionError(
            f"Module {module_name} does not have a matching test file. Expected {expected_test_file_path} to exist."
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
