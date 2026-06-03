from pathlib import Path

import pytest
from PIL import Image
from puremagic import from_file

from betty.dirs import BUILTIN_ASSET_DIRECTORY
from betty.entities.file import File
from betty.entities.file_reference import FileReference
from betty.job import Context
from betty.media_type import MediaType
from betty.media_types.svg import SVG
from betty.test_utils.ancestry.has_file_references import DummyHasFileReferences
from betty.test_utils.conftest import AssertTemplateString

_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH = (
    BUILTIN_ASSET_DIRECTORY / "public" / "static" / "betty-512x512.png"
)
_TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGNAMES = ("expected", "template", "filey")
_TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGVALUES = [
    (
        "betty-static:///file/F1-99x-.png",
        "{{ filey | image_resize_cover((99, none)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1--x99.png",
        "{{ filey | image_resize_cover((none, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1-99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1-99x99-1x2x3x4.png",
        "{{ filey | image_resize_cover((99, 99), focus=(1, 2, 3, 4)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1-99x99.png#betty-static:///file/F1-99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}#{{ filey | image_resize_cover((99, 99)) }}",
        File(
            id="F1",
            path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
            media_type=MediaType("image/png"),
        ),
    ),
    (
        "betty-static:///file/F1-99x99.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        FileReference(
            DummyHasFileReferences(),
            File(
                id="F1",
                path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
        ),
    ),
    (
        "betty-static:///file/F1-99x99-0x0x9x9.png",
        "{{ filey | image_resize_cover((99, 99)) }}",
        FileReference(
            DummyHasFileReferences(),
            File(
                id="F1",
                path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH,
                media_type=MediaType("image/png"),
            ),
            focus=(0, 0, 9, 9),
        ),
    ),
]


class TestImageResizeCover:
    @pytest.mark.parametrize(
        _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGNAMES,
        _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGVALUES,
    )
    async def test___call__(
        self,
        assert_template_string: AssertTemplateString,
        expected: str,
        template: str,
        filey: File,
    ) -> None:
        async with assert_template_string(
            template=template,
            data={
                "filey": filey,
            },
        ) as (actual, project):
            assert actual == expected
            for file in actual.split("#"):
                assert (project.www_directory / file[16:]).exists()

    @pytest.mark.parametrize(
        _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGNAMES,
        _TEST_FILTER_IMAGE_RESIZE_COVER_PARAMETER_ARGVALUES,
    )
    async def test___call____with_context(
        self,
        assert_template_string: AssertTemplateString,
        expected: str,
        template: str,
        filey: File,
    ) -> None:
        async with assert_template_string(
            template=template,
            data={
                "filey": filey,
                "context": Context(),
            },
        ) as (actual, project):
            assert actual == expected
            for file in actual.split("#"):
                assert (project.www_directory / file[16:]).exists()

    async def test___call____with_svg(
        self, assert_template_string: AssertTemplateString, tmp_path: Path
    ) -> None:
        image_path = tmp_path / "image.svg"
        with open(image_path, "w", encoding="utf-8") as f:
            f.write(
                '<?xml version="1.0" encoding="UTF-8"?><svg version="1.1" xmlns="http://www.w3.org/2000/svg"></svg>'
            )
        async with assert_template_string(
            template="{{ filey | image_resize_cover }}",
            data={
                "filey": File(
                    id="F1",
                    path=image_path,
                    media_type=SVG,
                )
            },
        ) as (actual, project):
            assert actual == "betty-static:///file/F1/file/image.svg"
            for file in actual.split("#"):
                assert (project.www_directory / file[16:]).exists()

    async def test___call____with_pdf(
        self, assert_template_string: AssertTemplateString, tmp_path: Path
    ) -> None:
        image_path = tmp_path / "image.pdf"
        image = Image.new("1", (1, 1))
        image.save(image_path)
        async with assert_template_string(
            template="{{ filey | image_resize_cover }}",
            data={
                "filey": File(
                    id="F1",
                    path=image_path,
                    media_type=MediaType("application/pdf"),
                )
            },
        ) as (actual, project):
            assert actual == "betty-static:///file/F1-.jpg"
            for public_file in actual.split("#"):
                file = project.www_directory / public_file[16:]
                assert file.exists()
                assert from_file(file, True) == "image/jpeg"

    async def test___call____with_invalid_image(
        self, assert_template_string: AssertTemplateString, tmp_path: Path
    ) -> None:
        file = tmp_path / "not-an-image.txt"
        file.touch()
        with pytest.raises(ValueError):  # noqa: PT011
            async with assert_template_string(
                template="{{ filey | image_resize_cover }}",
                data={
                    "filey": File(
                        id="F1",
                        path=file,
                        media_type=MediaType("text/plain"),
                    )
                },
            ):
                pass  # pragma: nocover

    async def test___call____with_file_without_media_type(
        self, assert_template_string: AssertTemplateString
    ) -> None:
        with pytest.raises(ValueError):  # noqa: PT011
            async with assert_template_string(
                template="{{ filey | image_resize_cover }}",
                data={
                    "filey": File(
                        id="F1", path=_TEST_FILTER_IMAGE_RESIZE_COVER_IMAGE_PATH
                    )
                },
            ):
                pass  # pragma: nocover
