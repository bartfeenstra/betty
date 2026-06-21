from ast import Constant, Expr, iter_child_nodes, parse
from contextlib import suppress
from pathlib import Path

import pytest

from betty.dirs import root_directory

python_directory = root_directory / "betty"
test_directory = python_directory / "tests"


def has_python_files(path: Path) -> bool:
    for _directory, _directory_names, file_names in path.walk():
        for file_name in file_names:
            if file_name.endswith(".py"):
                return True
    return False


def test_python_modules_have_init(subtests: pytest.Subtests) -> None:
    for directory, directory_names, file_names in python_directory.walk():
        with suppress(ValueError):
            directory_names.remove("__pycache__")
        python_file_names = tuple(
            file_name for file_name in file_names if file_name.endswith(".py")
        )
        with subtests.test():
            assert not python_file_names or "__init__.py" in file_names, (
                f"Failed asserting that {directory}/__init__.py exists."
            )


def test_python_source_modules_no_needless_directories(
    subtests: pytest.Subtests,
) -> None:
    for directory, directory_names, file_names in python_directory.walk():
        if directory.is_relative_to(test_directory):
            continue
        with suppress(ValueError):
            directory_names.remove("__pycache__")
        python_file_names = tuple(
            file_name for file_name in file_names if file_name.endswith(".py")
        )
        if python_file_names != ("__init__.py",):
            continue
        if any(
            has_python_files(directory / directory_name)
            for directory_name in directory_names
        ):
            continue

        with subtests.test():
            raise AssertionError(
                f"betty.{'.'.join(directory.relative_to(python_directory).parts)} does not have any submodules. Rename {directory}/__init__.py to {directory}.py and remove {directory}."
            )


def test_python_source_modules_have_from_future_import_annotations(
    subtests: pytest.Subtests,
) -> None:
    for directory, directory_names, file_names in python_directory.walk():
        if directory.is_relative_to(test_directory):
            continue
        with suppress(ValueError):
            directory_names.remove("__pycache__")
        for file_name in file_names:
            if not file_name.endswith(".py"):
                continue
            with open(directory / file_name, encoding="utf-8") as f:
                if (
                    "from __future__ import annotations" not in f.read()
                    and not _test_python_file_contains_docstring_only(
                        directory / file_name
                    )
                ):
                    with subtests.test():
                        raise AssertionError(
                            f"Failed asserting that {directory / file_name} contains `from __future__ import annotations`."
                        )


def _test_python_file_contains_docstring_only(file: Path, /) -> bool:
    with open(file, encoding="utf-8") as f:
        python = f.read()
    for child in iter_child_nodes(parse(python, file)):
        if not isinstance(child, Expr):
            return False
        if not isinstance(child.value, Constant):
            return False
    return True
