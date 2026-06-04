import pytest

from betty.dirs import root_directory


def test_python_modules(subtests: pytest.Subtests) -> None:
    for directory, _directory_names, file_names in (root_directory / "betty").walk():
        python_file_names = [
            file_name for file_name in file_names if file_name.endswith(".py")
        ]
        with subtests.test():
            assert not python_file_names or "__init__.py" in file_names, (
                f"Failed asserting that {directory}/__init__.py exists."
            )
