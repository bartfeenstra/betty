from collections.abc import Sequence
from pathlib import Path
from typing import Final

import pytest

from betty.dirs import builtin_asset_directory
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.job import Context
from betty.media_types import png
from betty.test_utils.associations.has_file_references import DummyHasFileReferences
from betty.test_utils.conftest import AssertJinja

_test_filter_image_resize_cover_image_path: Final[Path] = (
    builtin_asset_directory / "public" / "static" / "betty-512x512.png"
)
_test_filter_image_resize_cover_parameter_argnames: Final[tuple[str, str, str]] = (
    "expected",
    "template",
    "filey",
)
_test_filter_image_resize_cover_parameter_argvalues: Final[
    Sequence[tuple[str, str, File | FileReference]]
] = [
    (
        "betty-static:///file/my-first-file/file/image-resize-cover/99x-.png",
        "{{ filey | image_resize_cover((99, none)) }}",
        File(
            id="my-first-file",
            path=_test_filter_image_resize_cover_image_path,
            media_type=png,
        ),
    ),
    (
        "betty-static:///file/my-first-file/file/image-resize-cover/-x99.png",
        "{{ filey | image_resize_cover((none, 99)) }}",
        File(
            id="my-first-file",
            path=_test_filter_image_resize_cover_image_path,
            media_type=png,
        ),
    ),
    (
        "betty-static:///file/my-first-file/file/image-resize-cover/99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        File(
            id="my-first-file",
            path=_test_filter_image_resize_cover_image_path,
            media_type=png,
        ),
    ),
    (
        "betty-static:///file/my-first-file/file/image-resize-cover/99x99-1x2x3x4.png",
        "{{ filey | image_resize_cover((99, 99), focus=(1, 2, 3, 4)) }}",
        File(
            id="my-first-file",
            path=_test_filter_image_resize_cover_image_path,
            media_type=png,
        ),
    ),
    (
        "betty-static:///file/my-first-file/file/image-resize-cover/99x99.png#betty-static:///file/my-first-file/file/image-resize-cover/99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}#{{ filey | image_resize_cover((99, 99)) }}",
        File(
            id="my-first-file",
            path=_test_filter_image_resize_cover_image_path,
            media_type=png,
        ),
    ),
    (
        "betty-static:///file/my-first-file/file/image-resize-cover/99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        FileReference(
            DummyHasFileReferences(),
            File(
                id="my-first-file",
                path=_test_filter_image_resize_cover_image_path,
                media_type=png,
            ),
        ),
    ),
    (
        "betty-static:///file/my-first-file/file/image-resize-cover/99x99-0x0x9x9.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        FileReference(
            DummyHasFileReferences(),
            File(
                id="my-first-file",
                path=_test_filter_image_resize_cover_image_path,
                media_type=png,
            ),
            focus=(0, 0, 9, 9),
        ),
    ),
]


class TestImageResizeCover:
    @pytest.mark.parametrize(
        _test_filter_image_resize_cover_parameter_argnames,
        _test_filter_image_resize_cover_parameter_argvalues,
    )
    async def test___call__(
        self, assert_jinja_str: AssertJinja, expected: str, template: str, filey: File
    ) -> None:
        async with assert_jinja_str(template, data={"filey": filey}) as rendered:
            assert rendered == expected
            for file in rendered.split("#"):
                assert (assert_jinja_str.project.www_directory / file[16:]).exists()

    @pytest.mark.parametrize(
        _test_filter_image_resize_cover_parameter_argnames,
        _test_filter_image_resize_cover_parameter_argvalues,
    )
    async def test___call____with_context(
        self, assert_jinja_str: AssertJinja, expected: str, template: str, filey: File
    ) -> None:
        async with assert_jinja_str(
            template, data={"filey": filey, "context": Context()}
        ) as rendered:
            assert rendered == expected
            for file in rendered.split("#"):
                assert (assert_jinja_str.project.www_directory / file[16:]).exists()
