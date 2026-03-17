from pathlib import Path

import pytest

from betty.job import Context
from betty.plugins.entity.file import File
from betty.test_utils.conftest import AssertTemplateString

_TEST_FILTER_FILE_PARAMETER_ARGNAMES = ("expected", "template", "file")
_TEST_FILTER_FILE_PARAMETER_ARGVALUES = [
    (
        "betty-static:///file/F1/file/test_file.py",
        "{{ file | file }}",
        File(
            id="F1",
            path=Path(__file__),
        ),
    ),
    (
        "betty-static:///file/F1/file/test_file.py#betty-static:///file/F1/file/test_file.py",
        "{{ file | file }}#{{ file | file }}",
        File(
            id="F1",
            path=Path(__file__),
        ),
    ),
]


class TestFile:
    @pytest.mark.parametrize(
        _TEST_FILTER_FILE_PARAMETER_ARGNAMES, _TEST_FILTER_FILE_PARAMETER_ARGVALUES
    )
    async def test___call__(
        self,
        assert_template_string: AssertTemplateString,
        expected: str,
        template: str,
        file: File,
    ) -> None:
        async with assert_template_string(
            template=template,
            data={
                "file": file,
            },
        ) as (actual, project):
            assert actual == expected
            for file_path in actual.split("#"):
                assert (project.www_directory / file_path[16:]).exists()

    @pytest.mark.parametrize(
        _TEST_FILTER_FILE_PARAMETER_ARGNAMES, _TEST_FILTER_FILE_PARAMETER_ARGVALUES
    )
    async def test___call____with_context(
        self,
        assert_template_string: AssertTemplateString,
        expected: str,
        template: str,
        file: File,
    ) -> None:
        async with assert_template_string(
            template=template,
            data={
                "file": file,
                "context": Context(),
            },
        ) as (actual, project):
            assert actual == expected
            for file_path in actual.split("#"):
                assert (project.www_directory / file_path[16:]).exists()
