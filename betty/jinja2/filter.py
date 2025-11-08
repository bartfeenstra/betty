"""
Provide Betty's default Jinja2 filters.
"""

from __future__ import annotations

import json as stdjson
import re
import warnings
from asyncio import get_running_loop, run
from contextlib import suppress
from io import BytesIO
from typing import TYPE_CHECKING, Any, TypeVar
from urllib.parse import quote

import aiofiles
from aiofiles.os import makedirs
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import pass_context, pass_eval_context
from jinja2.async_utils import auto_aiter, auto_await
from jinja2.filters import make_attrgetter, prepare_map
from jinja2.runtime import Context, Macro
from markupsafe import Markup
from pdf2image.pdf2image import convert_from_path
from PIL import Image
from PIL.Image import DecompressionBombWarning

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.hashid import hashid, hashid_file_meta
from betty.html import newlines_to_paragraphs
from betty.image import (
    FocusArea,
    Size,
    image_file_path_format,
    resize_cover,
)
from betty.locale import (
    SPECIAL_LOCALES,
    UNDETERMINED_LOCALE,
    LocaleLike,
    get_data,
    negotiate_locale,
)
from betty.locale.error import LocaleError
from betty.locale.localized import LocalizedStr
from betty.media_type import MediaType
from betty.media_type.media_types import HTML, SVG
from betty.os import link_or_copy
from betty.string import (
    camel_case_to_kebab_case,
    camel_case_to_snake_case,
    upper_camel_case_to_lower_camel_case,
)
from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Callable,
        Iterable,
        Iterator,
        Mapping,
    )
    from pathlib import Path

    from jinja2.nodes import EvalContext

    from betty.ancestry.date import HasDate
    from betty.date import DateLike
    from betty.locale.localizable import Localizable
    from betty.locale.localized import Localized

_T = TypeVar("_T")


@pass_context
async def filter_url(
    context: Context,
    resource: Any,
    locale: LocaleLike | None = None,
    media_type: str | None = None,
    **kwargs: Any,
) -> str:
    """
    Generate a URL for a resource.
    """
    from betty.jinja2 import context_localizer, context_project

    url_generator = await context_project(context).url_generator
    return url_generator.generate(
        resource,
        media_type=MediaType(media_type) if media_type else HTML,
        locale=locale or context_localizer(context).locale,
        **kwargs,
    )


@pass_context
def filter_localize(
    context: Context,
    localizable: Localizable,
) -> str:
    """
    Localize a value using the context's current localizer.
    """
    from betty.jinja2 import context_localizer

    return localizable.localize(context_localizer(context))


_CHARACTER_ORDER_TO_HTML_LANG_MAP = {
    "left-to-right": "ltr",
    "right-to-left": "rtl",
}


@pass_context
def filter_html_lang(context: Context, localized: str) -> str | Markup:
    """
    Optionally add the necessary HTML to indicate the localized string has a different locale than the surrounding HTML.
    """
    from betty.jinja2 import context_localizer

    if not isinstance(localized, LocalizedStr):
        return localized

    localizer = context_localizer(context)
    result: str | Markup = localized
    if localized.locale != localizer.locale:
        localizer_locale_data = get_data(localizer.locale)
        localizer_dir = _CHARACTER_ORDER_TO_HTML_LANG_MAP[
            localizer_locale_data.character_order
        ]
        try:
            localized_locale_data = get_data(localized.locale)
        except LocaleError:
            localized_dir = "auto"
        else:
            localized_dir = _CHARACTER_ORDER_TO_HTML_LANG_MAP[
                localized_locale_data.character_order
            ]
        dir_attribute = (
            f' dir="{localized_dir}"' if localized_dir != localizer_dir else ""
        )
        result = f'<span lang="{localized.locale}"{dir_attribute}>{localized}</span>'
    if context.eval_ctx.autoescape:
        result = Markup(result)
    return result


@pass_context
def filter_format_date_like(
    context: Context,
    date_like: DateLike,
) -> str:
    """
    Format a :py:type:`betty.date.DateLike`.
    """
    from betty.jinja2 import context_localizer

    return context_localizer(context).format_date_like(date_like)


def filter_json_dump(data: Any, indent: int | None = None) -> str:
    """
    Dump a value to a JSON string.
    """
    return stdjson.dumps(data, indent=indent)


def filter_json_load(data: str) -> Any:
    """
    Load a value from a JSON string.
    """
    return stdjson.loads(data)


async def filter_flatten(values_of_values: Iterable[Iterable[_T]]) -> AsyncIterator[_T]:
    """
    Flatten an iterable of iterables into a single iterable.
    """
    async for values in auto_aiter(values_of_values):
        async for value in auto_aiter(values):
            yield value


_paragraph_re = re.compile(r"(?:\r\n|\r|\n){2,}")


@pass_eval_context
def filter_paragraphs(eval_ctx: EvalContext, text: str) -> str | Markup:
    """
    Convert newlines to <p> and <br> tags.

    Taken from http://jinja.pocoo.org/docs/2.10/api/#custom-filters.
    """
    result = newlines_to_paragraphs(text)
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def filter_format_degrees(degrees: int) -> str:
    """
    Format geographic coordinates.
    """
    arcminutes = units.arcminutes(degrees=degrees - int(degrees))
    arcseconds = units.arcseconds(arcminutes=arcminutes - int(arcminutes))
    format_dict = {
        "deg": "°",
        "arcmin": "'",
        "arcsec": '"',
        "degrees": degrees,
        "minutes": round(abs(arcminutes)),
        "seconds": round(abs(arcseconds)),
    }
    return DEGREES_FORMAT % format_dict  # type: ignore[no-any-return]


async def filter_unique(values: Iterable[_T]) -> AsyncIterator[_T]:
    """
    Iterate over an iterable of values and only yield those values that have not been yielded before.
    """
    seen = []
    async for value in auto_aiter(values):
        if value not in seen:
            yield value
            seen.append(value)


@pass_context
async def filter_map(
    context: Context, values: Iterable[Any], *args: Any, **kwargs: Any
) -> Any:
    """
    Map an iterable's values.

    This mimics Jinja2's built-in map filter, but allows macros as callbacks.
    """
    if len(args) > 0 and isinstance(args[0], Macro):
        func: Macro | Callable[[Any], bool] = args[0]
    else:
        func = prepare_map(context, args, kwargs)
    async for value in auto_aiter(values):
        yield await auto_await(func(value))


@pass_context
async def filter_file(context: Context, file: File) -> str:
    """
    Preprocess a file for use in a page.

    :return: A ``betty-static://`` URL resource from which a public URL can be generated.
    """
    from betty.jinja2 import context_job_context, context_project

    project = context_project(context)
    job_context = context_job_context(context)

    execute_filter = True
    if job_context:
        job_cache_item_id = f"filter_file:{file.id}"
        async with job_context.cache.hasset(job_cache_item_id) as setter:
            if setter:
                await setter(True)
            else:
                execute_filter = False
    if execute_filter:
        file_destination_path = (
            project.configuration.www_directory_path
            / "file"
            / file.id
            / "file"
            / file.name
        )
        await makedirs(file_destination_path.parent, exist_ok=True)
        await link_or_copy(file.path, file_destination_path)

    return f"betty-static:///file/{quote(file.id)}/file/{quote(file.name)}"


@pass_context
async def filter_image_resize_cover(
    context: Context,
    filey: File | FileReference,
    size: Size | None = None,
    *,
    focus: FocusArea | None = None,
) -> str:
    """
    Preprocess an image file for use in a page.

    :return: A ``betty-static://`` URL resource from which a public URL can be generated.
    """
    from betty.jinja2 import context_job_context, context_project

    file = filey if isinstance(filey, File) else filey.file
    assert file is not None
    file_reference = filey if isinstance(filey, FileReference) else None

    if (
        focus is None
        and file_reference is not None
        and file_reference.focus is not None
    ):
        focus = file_reference.focus

    # Treat SVGs as regular files.
    if file.media_type and file.media_type == SVG:
        return await filter_file(context, file)

    project = context_project(context)
    job_context = context_job_context(context)

    destination_name = f"{file.id}-"
    if size is not None:
        width, height = size
        if width is None:
            destination_name += f"-x{height}"
        elif height is None:
            destination_name += f"{width}x-"
        else:
            destination_name += f"{width}x{height}"
    if focus is not None:
        destination_name += f"-{focus[0]}x{focus[1]}x{focus[2]}x{focus[3]}"

    file_directory_path = project.configuration.www_directory_path / "file"

    if file.media_type:
        if file.media_type.type == "image":
            image_loader = _load_image_image
            destination_name += file.path.suffix
        elif file.media_type.type == "application" and file.media_type.subtype == "pdf":
            image_loader = _load_image_application_pdf
            destination_name += "." + "jpg"
        else:
            raise ValueError(
                f'Cannot convert a file of media type "{file.media_type}" to an image.'
            )
    else:
        raise ValueError("Cannot convert a file without a media type to an image.")

    cache_item_id = f"{await hashid_file_meta(file.path)}:{destination_name}"
    execute_filter = True
    if job_context:
        async with job_context.cache.with_scope("filter_image").hasset(
            cache_item_id
        ) as setter:
            if setter:
                await setter(True)
            else:
                execute_filter = False
    if execute_filter:
        loop = get_running_loop()
        await loop.run_in_executor(
            project.app.process_pool,
            _execute_filter_image,
            image_loader,
            file.path,
            project.app.binary_file_cache.with_scope("image").cache_item_file_path(
                cache_item_id
            ),
            file_directory_path,
            destination_name,
            size,
            focus,
        )
    return f"betty-static:///file/{quote(destination_name)}"


async def _load_image_image(file_path: Path) -> Image.Image:
    # We want to read the image asynchronously and prevent Pillow from keeping too many file
    # descriptors open simultaneously, so we read the image ourselves and store the contents
    # in a synchronous file object.
    async with aiofiles.open(file_path, "rb") as f:
        image_f = BytesIO(await f.read())
    # Ignore warnings about decompression bombs, because we know where the files come from.
    with warnings.catch_warnings(action="ignore", category=DecompressionBombWarning):
        return Image.open(image_f, formats=[image_file_path_format(file_path)])


async def _load_image_application_pdf(file_path: Path) -> Image.Image:
    # Ignore warnings about decompression bombs, because we know where the files come from.
    with warnings.catch_warnings(action="ignore", category=DecompressionBombWarning):
        return convert_from_path(file_path)[0]


def _execute_filter_image(
    image_loader: Callable[[Path], Awaitable[Image.Image]],
    file_path: Path,
    cache_item_file_path: Path,
    destination_directory_path: Path,
    destination_name: str,
    size: Size | None,
    focus: FocusArea | None,
) -> None:
    run(
        __execute_filter_image(
            image_loader,
            file_path,
            cache_item_file_path,
            destination_directory_path,
            destination_name,
            size,
            focus,
        )
    )


async def __execute_filter_image(
    image_loader: Callable[[Path], Awaitable[Image.Image]],
    file_path: Path,
    cache_item_file_path: Path,
    destination_directory_path: Path,
    destination_name: str,
    size: Size | None,
    focus: FocusArea | None,
) -> None:
    destination_file_path = destination_directory_path / destination_name
    await makedirs(destination_directory_path, exist_ok=True)

    # If no customizations are needed, work straight from the source.
    if size is None and file_path.suffix == destination_file_path.suffix:
        await link_or_copy(file_path, destination_file_path)
        return

    try:
        # Try using a previously cached image.
        await link_or_copy(cache_item_file_path, destination_file_path)
    except FileNotFoundError:
        # Apply customizations, and cache the customized image.
        original_image = converted_image = await image_loader(file_path)
        try:
            await makedirs(cache_item_file_path.parent, exist_ok=True)
            if size is not None:
                converted_image = resize_cover(converted_image, size, focus=focus)
            converted_image.save(
                cache_item_file_path,
                format=image_file_path_format(destination_file_path),
            )
            del converted_image
        finally:
            original_image.close()
            del original_image
        await link_or_copy(cache_item_file_path, destination_file_path)


@pass_context
def filter_negotiate_localizeds(
    context: Context, localizeds: Iterable[Localized]
) -> Localized | None:
    """
    Try to find an object whose locale matches the context's current locale.
    """
    from betty.jinja2 import context_localizer
    from betty.locale import localized

    return localized.negotiate_localizeds(
        context_localizer(context).locale, list(localizeds)
    )


@pass_context
def filter_sort_localizeds(
    context: Context,
    localizeds: Iterable[Localized],
    localized_attribute: str,
    sort_attribute: str,
) -> Iterable[Localized]:
    """
    Sort localized objects.
    """
    get_localized_attr = make_attrgetter(context.environment, localized_attribute)
    get_sort_attr = make_attrgetter(context.environment, sort_attribute)

    def _get_sort_key(x: Localized) -> Any:
        return get_sort_attr(
            filter_negotiate_localizeds(context, get_localized_attr(x))
        )

    return sorted(localizeds, key=_get_sort_key)


@pass_context
def filter_select_localizeds(
    context: Context, localizeds: Iterable[Localized], include_unspecified: bool = False
) -> Iterable[Localized]:
    """
    Select all objects whose locale matches the context's current locale.

    :param include_unspecified: If True, the return value includes all objects that do not have a locale specified.
    """
    from betty.jinja2 import context_localizer

    for localized in localizeds:
        if include_unspecified and localized.locale in {
            None,
            *SPECIAL_LOCALES,
        }:
            yield localized
        if (
            localized.locale is not UNDETERMINED_LOCALE
            and negotiate_locale(context_localizer(context).locale, [localized.locale])
            is not None
        ):
            yield localized


@pass_context
def filter_negotiate_has_dates(
    context: Context, has_dates: Iterable[HasDate], date: DateLike | None
) -> HasDate | None:
    """
    Try to find an object whose date falls in the given date.

    :param date: A date to select by. If ``None``, then today's date is used.
    """
    with suppress(StopIteration):
        return next(filter_select_has_dates(context, has_dates, date))
    return None


@pass_context
def filter_select_has_dates(
    context: Context, has_dates: Iterable[HasDate], date: DateLike | None
) -> Iterator[HasDate]:
    """
    Select all objects whose date falls in the given date.

    :param date: A date to select by. If ``None``, then today's date is used.
    """
    if date is None:
        date = context.resolve_or_missing("today")
    return filter(
        lambda dated: dated.date is None
        or dated.date.comparable
        and dated.date in date,
        has_dates,
    )


locale_get_data = get_data


@internal
async def filters() -> Mapping[str, Callable[..., Any]]:
    """
    Define the available filters.
    """
    return {
        "camel_case_to_kebab_case": camel_case_to_kebab_case,
        "camel_case_to_snake_case": camel_case_to_snake_case,
        "file": filter_file,
        "flatten": filter_flatten,
        "format_date_like": filter_format_date_like,
        "format_degrees": filter_format_degrees,
        "hashid": hashid,
        "image_resize_cover": filter_image_resize_cover,
        "html_lang": filter_html_lang,
        "json_dump": filter_json_dump,
        "json_load": filter_json_load,
        "locale_get_data": locale_get_data,
        "localize": filter_localize,
        "map": filter_map,
        "negotiate_has_dates": filter_negotiate_has_dates,
        "negotiate_localizeds": filter_negotiate_localizeds,
        "paragraphs": filter_paragraphs,
        "select_has_dates": filter_select_has_dates,
        "select_localizeds": filter_select_localizeds,
        "sort_localizeds": filter_sort_localizeds,
        "str": str,
        "unique": filter_unique,
        "upper_camel_case_to_lower_camel_case": upper_camel_case_to_lower_camel_case,
        "url": filter_url,
    }
