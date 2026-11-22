import pytest

from betty.entities.file import File
from betty.test_utils.conftest import AssertJinja


class TestFileUrl:
    @pytest.mark.parametrize(
        ("expected", "absolute"),
        [
            ("https://example.com/file/my-first-file/file/test_file_url.py", True),
            ("/file/my-first-file/file/test_file_url.py", False),
        ],
    )
    async def test___call__(
        self, assert_jinja_str: AssertJinja, expected: str, absolute: bool
    ) -> None:
        file = File(__file__, id="my-first-file")
        template = "{{ file | file_url(absolute=absolute) }}"
        async with assert_jinja_str(
            template, data={"file": file, "absolute": absolute}
        ) as rendered:
            assert rendered == expected
