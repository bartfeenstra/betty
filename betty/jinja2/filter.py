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
from typing import (
    Callable,
    Iterable,
    Any,
    Iterator,
    TypeVar,
    AsyncIterator,
    TYPE_CHECKING,
)
from urllib.parse import quote

import aiofiles
from PIL import Image
from PIL.Image import DecompressionBombWarning
from aiofiles.os import makedirs
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import pass_context, pass_eval_context
from jinja2.async_utils import auto_aiter, auto_await
from jinja2.filters import prepare_map, make_attrgetter
from jinja2.runtime import Context, Macro
from markupsafe import Markup, escape
from pdf2image.pdf2image import convert_from_path

from betty.ancestry.file import File
from betty.ancestry.file_reference import FileReference
from betty.hashid import hashid_file_meta, hashid
from betty.image import resize_cover, Size, FocusArea
from betty.locale import (
    negotiate_locale,
    Localey,
    get_data,
    UNDETERMINED_LOCALE,
    SPECIAL_LOCALES,
)
from betty.locale.localized import Localized, negotiate_localizeds, LocalizedStr
from betty.media_type import MediaType
from betty.media_type.media_types import HTML, SVG
from betty.os import link_or_copy
from betty.string import (
    camel_case_to_snake_case,
    camel_case_to_kebab_case,
    upper_camel_case_to_lower_camel_case,
)
from betty.typing import internal

if TYPE_CHECKING:
    from betty.ancestry.date import HasDate
    from betty.date import Datey
    from betty.locale.localizable import Localizable
    from jinja2.nodes import EvalContext
    from pathlib import Path
    from collections.abc import Awaitable, Mapping

_T = TypeVar("_T")


@pass_context
async def filter_localized_url(
    context: Context,
    resource: Any,
    locale: Localey | None = None,
    media_type: str | None = None,
    **kwargs: Any,
) -> str:
    """
    Generate a localized URL for a localizable resource.
    """
    from betty.jinja2 import context_project, context_localizer

    localized_url_generator = await context_project(context).localized_url_generator
    return localized_url_generator.generate(
        resource,
        MediaType(media_type) if media_type else HTML,
        locale=locale or context_localizer(context).locale,
        **kwargs,
    )


@pass_context
async def filter_static_url(
    context: Context,
    resource: Any,
    absolute: bool = False,
) -> str:
    """
    Generate a static URL for a static resource.
    """
    from betty.jinja2 import context_project

    static_url_generator = await context_project(context).static_url_generator
    return static_url_generator.generate(resource, absolute=absolute)


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


@pass_context
def filter_localize_html_lang(
    context: Context,
    localizable: Localizable,
) -> str | Markup:
    """
    Localize a value using the context's current localizer.

    This optionally adds the necessary HTML that indicates the localized
    string is of a different locale than the surrounding HTML.
    """
    from betty.jinja2 import context_localizer

    localizer = context_localizer(context)
    localized = localizable.localize(localizer)
    return filter_html_lang(context, localized)


@pass_context
def filter_html_lang(
    context: Context,
    localized: LocalizedStr,
) -> str | Markup:
    """
    Optionally add the necessary HTML to indicate the localized string has a different locale than the surrounding HTML.
    """
    from betty.jinja2 import context_localizer

    localizer = context_localizer(context)
    result: str | Markup = localized
    if localized.locale != localizer.locale:
        result = f'<span lang="{localized.locale}">{localized}</span>'
    if context.eval_ctx.autoescape:
        result = Markup(result)
    return result


@pass_context
def filter_format_datey(
    context: Context,
    datey: Datey,
) -> str:
    """
    Format a date or a date range.
    """
    from betty.jinja2 import context_localizer

    return context_localizer(context).format_datey(datey)


def filter_json(data: Any, indent: int | None = None) -> str:
    """
    Convert a value to a JSON string.
    """
    return stdjson.dumps(data, indent=indent)


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
    result = "\n\n".join(
        "<p>%s</p>" % p.replace("\n", Markup("<br>\n"))
        for p in _paragraph_re.split(escape(text))
    )
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

    :return: The public path to the preprocessed file. This can be used on a web page.
    """
    from betty.jinja2 import context_project, context_job_context

    project = context_project(context)
    job_context = context_job_context(context)

    execute_filter = True
    if job_context:
        job_cache_item_id = f"filter_file:{file.id}"
        async with job_context.cache.getset(job_cache_item_id, wait=False) as (
            cache_item,
            setter,
        ):
            if cache_item is None and setter is not None:
                await setter(None)
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

    return f"/file/{quote(file.id)}/file/{quote(file.name)}"


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

    :return: The public path to the preprocessed file. This can be embedded in a web page.
    """
    from betty.jinja2 import context_project, context_job_context

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
        async with job_context.cache.with_scope("filter_image").getset(
            cache_item_id, wait=False
        ) as (cache_item, setter):
            if cache_item is None and setter is not None:
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
            file.media_type,
            project.app.binary_file_cache.with_scope("image").cache_item_file_path(
                cache_item_id
            ),
            file_directory_path,
            destination_name,
            size,
            focus,
        )
    destination_public_path = f"/file/{quote(destination_name)}"

    return destination_public_path


async def _load_image_image(
    file_path: Path,
    media_type: MediaType,
) -> Image.Image:
    # We want to read the image asynchronously and prevent Pillow from keeping too many file
    # descriptors open simultaneously, so we read the image ourselves and store the contents
    # in a synchronous file object.
    async with aiofiles.open(file_path, "rb") as f:
        image_f = BytesIO(await f.read())
    # Ignore warnings about decompression bombs, because we know where the files come from.
    with warnings.catch_warnings(action="ignore", category=DecompressionBombWarning):
        image = Image.open(image_f, formats=[media_type.subtype])
    return image


async def _load_image_application_pdf(
    file_path: Path,
    media_type: MediaType,
) -> Image.Image:
    # Ignore warnings about decompression bombs, because we know where the files come from.
    with warnings.catch_warnings(action="ignore", category=DecompressionBombWarning):
        image = convert_from_path(file_path, fmt="jpeg")[0]
    return image


def _execute_filter_image(
    image_loader: Callable[[Path, MediaType], Awaitable[Image.Image]],
    file_path: Path,
    media_type: MediaType,
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
            media_type,
            cache_item_file_path,
            destination_directory_path,
            destination_name,
            size,
            focus,
        )
    )


async def __execute_filter_image(
    image_loader: Callable[[Path, MediaType], Awaitable[Image.Image]],
    file_path: Path,
    media_type: MediaType,
    cache_item_file_path: Path,
    destination_directory_path: Path,
    destination_name: str,
    size: Size | None,
    focus: FocusArea | None,
) -> None:
    destination_file_path = destination_directory_path / destination_name
    await makedirs(destination_directory_path, exist_ok=True)

    # If no customizations are needed, work straight from the source.
    if size is None:
        await link_or_copy(file_path, destination_file_path)
        return

    try:
        # Try using a previously cached image.
        await link_or_copy(cache_item_file_path, destination_file_path)
    except FileNotFoundError:
        # Apply customizations, and cache the customized image.
        image = await image_loader(file_path, media_type)
        try:
            await makedirs(cache_item_file_path.parent, exist_ok=True)
            converted_image = resize_cover(image, size, focus=focus)
            converted_image.save(cache_item_file_path, format=media_type.subtype)
            del converted_image
        finally:
            image.close()
            del image
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
    from betty.jinja2 import context_localizer

    get_localized_attr = make_attrgetter(context.environment, localized_attribute)
    get_sort_attr = make_attrgetter(context.environment, sort_attribute)

    def _get_sort_key(x: Localized) -> Any:
        return get_sort_attr(
            negotiate_localizeds(
                context_localizer(context).locale, get_localized_attr(x)
            )
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
    context: Context, has_dates: Iterable[HasDate], date: Datey | None
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
    context: Context, has_dates: Iterable[HasDate], date: Datey | None
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


def filter_hashid(source: str) -> str:
    """
    Create a hash ID.
    """
    return hashid(source)


@pass_context
def filter_public_css(context: Context, public_path: str) -> None:
    """
    Add a CSS file to the current page.
    """
    context.resolve_or_missing("public_css_paths").add(public_path)


@pass_context
def filter_public_js(context: Context, public_path: str) -> None:
    """
    Add a JavaScript file to the current page.
    """
    context.resolve_or_missing("public_js_paths").add(public_path)


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
        "format_datey": filter_format_datey,
        "format_degrees": filter_format_degrees,
        "hashid": filter_hashid,
        "filter_image_resize_cover": filter_image_resize_cover,
        "html_lang": filter_html_lang,
        "json": filter_json,
        "locale_get_data": get_data,
        "localize": filter_localize,
        "localize_html_lang": filter_localize_html_lang,
        "localized_url": filter_localized_url,
        "map": filter_map,
        "negotiate_has_dates": filter_negotiate_has_dates,
        "negotiate_localizeds": filter_negotiate_localizeds,
        "paragraphs": filter_paragraphs,
        "select_has_dates": filter_select_has_dates,
        "select_localizeds": filter_select_localizeds,
        "static_url": filter_static_url,
        "sort_localizeds": filter_sort_localizeds,
        "str": str,
        "unique": filter_unique,
        "upper_camel_case_to_lower_camel_case": upper_camel_case_to_lower_camel_case,
        "public_css": filter_public_css,
        "public_js": filter_public_js,
    }
