from collections.abc import Sequence
from typing import Final

import pytest

from betty.entities.file import File
from betty.job import Context
from betty.test_utils.conftest import AssertJinja

_test_filter_file_parameter_argnames: Final[tuple[str, str, str]] = (
    "expected",
    "template",
    "file",
)
_test_filter_file_parameter_argvalues: Final[Sequence[tuple[str, str, File]]] = [
    (
        "betty-static:///file/my-first-file/file/test_file.py",
        "{{ file | file }}",
        File(id="my-first-file", path=__file__),
    ),
    (
        "betty-static:///file/my-first-file/file/test_file.py#betty-static:///file/my-first-file/file/test_file.py",
        "{{ file | file }}#{{ file | file }}",
        File(id="my-first-file", path=__file__),
    ),
]


class TestFile:
    @pytest.mark.parametrize(
        _test_filter_file_parameter_argnames, _test_filter_file_parameter_argvalues
    )
    async def test___call__(
        self, assert_jinja_str: AssertJinja, expected: str, template: str, file: File
    ) -> None:
        async with assert_jinja_str(template, data={"file": file}) as rendered:
            assert rendered == expected
            for file_path in rendered.split("#"):
                assert (
                    assert_jinja_str.project.www_directory / file_path[16:]
                ).exists()

    @pytest.mark.parametrize(
        _test_filter_file_parameter_argnames, _test_filter_file_parameter_argvalues
    )
    async def test___call____with_context(
        self, assert_jinja_str: AssertJinja, expected: str, template: str, file: File
    ) -> None:
        async with assert_jinja_str(
            template, data={"file": file, "context": Context()}
        ) as rendered:
            assert rendered == expected
            for file_path in rendered.split("#"):
                assert (
                    assert_jinja_str.project.www_directory / file_path[16:]
                ).exists()
