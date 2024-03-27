"""
Provide Betty's default Jinja2 filters.
"""
from __future__ import annotations

import json as stdjson
import re
import warnings
from asyncio import get_running_loop
from base64 import b64encode
from collections.abc import Awaitable
from contextlib import suppress
from io import BytesIO
from pathlib import Path
from typing import Callable, Iterable, Any, Iterator, TypeVar, AsyncIterator
from urllib.parse import quote

import aiofiles
from PIL import Image
from PIL.Image import DecompressionBombWarning
from aiofiles.os import makedirs
from geopy import units
from geopy.format import DEGREES_FORMAT
from jinja2 import pass_context, \
    pass_eval_context
from jinja2.async_utils import auto_aiter, auto_await
from jinja2.filters import prepare_map, make_attrgetter
from jinja2.nodes import EvalContext
from jinja2.runtime import Context, Macro
from markupsafe import Markup, escape
from pdf2image.pdf2image import convert_from_path

from betty import _resizeimage
from betty.asyncio import sync
from betty.fs import hashfile
from betty.functools import walk
from betty.locale import negotiate_localizeds, Localized, Datey, negotiate_locale, Localey, get_data, Localizable
from betty.media_type import MediaType
from betty.model import get_entity_type_name
from betty.model.ancestry import File, Dated
from betty.os import link_or_copy
from betty.serde.dump import minimize, none_void, void_none
from betty.string import camel_case_to_snake_case, camel_case_to_kebab_case, upper_camel_case_to_lower_camel_case

T = TypeVar('T')


@pass_context
def filter_url(
    context: Context,
    resource: Any,
    media_type: str | None = None,
    *args: Any,
    locale: Localey | None = None,
    **kwargs: Any,
) -> str:
    """
    Generate a localized URL for a localizable resource.
    """
    from betty.jinja2 import context_app, context_localizer

    return context_app(context).url_generator.generate(
        resource,
        media_type or 'text/html',
        *args,
        locale=locale or context_localizer(context).locale,  # type: ignore[misc]
        **kwargs,
    )


@pass_context
def filter_static_url(
    context: Context,
    resource: Any,
    absolute: bool = False,
) -> str:
    """
    Generate a static URL for a static resource.
    """
    from betty.jinja2 import context_app

    return context_app(context).static_url_generator.generate(
        resource,
        absolute=absolute,
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


async def filter_flatten(values_of_values: Iterable[Iterable[T]]) -> AsyncIterator[T]:
    """
    Flatten an iterable of iterables into a single iterable.
    """
    async for values in auto_aiter(values_of_values):
        async for value in auto_aiter(values):
            yield value


def filter_walk(value: Any, attribute_name: str) -> Iterable[Any]:
    """
    Walk over a data structure.
    """
    return walk(value, attribute_name)


_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')


@pass_eval_context
def filter_paragraphs(eval_ctx: EvalContext, text: str) -> str | Markup:
    """
    Convert newlines to <p> and <br> tags.

    Taken from http://jinja.pocoo.org/docs/2.10/api/#custom-filters.
    """
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', Markup('<br>\n'))
                          for p in _paragraph_re.split(escape(text)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def filter_format_degrees(degrees: int) -> str:
    """
    Format geographic coordinates.
    """
    arcminutes = units.arcminutes(degrees=degrees - int(degrees))
    arcseconds = units.arcseconds(arcminutes=arcminutes - int(arcminutes))
    format_dict = dict(
        deg='°',
        arcmin="'",
        arcsec='"',
        degrees=degrees,
        minutes=round(abs(arcminutes)),
        seconds=round(abs(arcseconds))
    )
    return DEGREES_FORMAT % format_dict  # type: ignore[no-any-return]


async def filter_unique(value: Iterable[T]) -> AsyncIterator[T]:
    """
    Iterate over an iterable of values and only yield those values that have not been yielded before.
    """
    seen = []
    async for value in auto_aiter(value):
        if value not in seen:
            yield value
            seen.append(value)


@pass_context
async def filter_map(context: Context, values: Iterable[Any], *args: Any, **kwargs: Any) -> Any:
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
    from betty.jinja2 import context_app, context_job_context

    app = context_app(context)
    job_context = context_job_context(context)

    if job_context is None or job_context.claim(f'filter_file:{file.id}'):
        file_destination_path = app.project.configuration.www_directory_path / 'file' / file.id / 'file' / file.path.name
        await makedirs(file_destination_path.parent, exist_ok=True)
        await link_or_copy(file.path, file_destination_path)

    return f'/file/{quote(file.id)}/file/{quote(file.path.name)}'


@pass_context
async def filter_image(
    context: Context,
    file: File,
    width: int | None = None,
    height: int | None = None,
) -> str:
    """
    Preprocess an image file for use in a page.

    :return: The public path to the preprocessed file. This can be embedded in a web page.
    """
    from betty.jinja2 import context_app, context_job_context

    # Treat SVGs as regular files.
    if file.media_type and file.media_type.type == 'image' and 'svg+xml' == file.media_type.subtype:
        return await filter_file(context, file)

    app = context_app(context)
    job_context = context_job_context(context)

    destination_name = f'{file.id}-'
    if height and width:
        destination_name += f'{width}x{height}'
    elif height:
        destination_name += f'-x{height}'
    elif width:
        destination_name += f'{width}x-'
    else:
        raise ValueError('At least the width or height must be given.')

    file_directory_path = app.project.configuration.www_directory_path / 'file'

    if file.media_type:
        if file.media_type.type == 'image':
            image_loader = _load_image_image
            destination_name += file.path.suffix
        elif file.media_type.type == 'application' and file.media_type.subtype == 'pdf':
            image_loader = _load_image_application_pdf
            destination_name += '.' + 'jpg'
        else:
            raise ValueError(f'Cannot convert a file of media type "{file.media_type}" to an image.')
    else:
        raise ValueError('Cannot convert a file without a media type to an image.')

    cache_item_id = f'filter_image:{hashfile(file.path)}:{"" if width is None else width}:{"" if height is None else height}'
    if job_context is None or job_context.claim(cache_item_id):
        loop = get_running_loop()
        await loop.run_in_executor(
            app.process_pool,
            _execute_filter_image,
            image_loader,
            file.path,
            file.media_type,
            app.cache.path / 'image' / filter_base64(cache_item_id),
            file_directory_path,
            destination_name,
            width,
            height,
        )

    destination_public_path = f'/file/{quote(destination_name)}'

    return destination_public_path


async def _load_image_image(
    file_path: Path,
    media_type: MediaType,
) -> Image:
    # We want to read the image asynchronously and prevent Pillow from keeping too many file
    # descriptors open simultaneously, so we read the image ourselves and store the contents
    # in a synchronous file object.
    async with aiofiles.open(file_path, 'rb') as f:
        image_f = BytesIO(await f.read())
    # Ignore warnings about decompression bombs, because we know where the files come from.
    with warnings.catch_warnings(action='ignore', category=DecompressionBombWarning):
        image = Image.open(image_f, formats=[media_type.subtype])
    return image


async def _load_image_application_pdf(
    file_path: Path,
    media_type: MediaType,
) -> Image:
    # Ignore warnings about decompression bombs, because we know where the files come from.
    with warnings.catch_warnings(action='ignore', category=DecompressionBombWarning):
        image = convert_from_path(file_path, fmt='jpeg')[0]
    return image


@sync
async def _execute_filter_image(
    image_loader: Callable[[Path, MediaType], Awaitable[Image]],
    file_path: Path,
    media_type: MediaType,
    cache_item_file_path: Path,
    destination_directory_path: Path,
    destination_name: str,
    width: int | None,
    height: int | None,
) -> None:
    destination_file_path = destination_directory_path / destination_name
    await makedirs(destination_directory_path, exist_ok=True)
    try:
        await link_or_copy(cache_item_file_path, destination_file_path)
    except FileNotFoundError:
        image = await image_loader(file_path, media_type)
        try:
            if width is not None:
                width = min(width, image.width)
            if height is not None:
                height = min(height, image.height)

            await makedirs(cache_item_file_path.parent, exist_ok=True)
            converted_image = await _execute_filter_image_convert(image, width, height)
            converted_image.save(cache_item_file_path, format=media_type.subtype)
            del converted_image
        finally:
            image.close()
            del image
        await link_or_copy(cache_item_file_path, destination_file_path)


async def _execute_filter_image_convert(
    image: Image,
    width: int | None,
    height: int | None,
) -> Image:
    if width is not None and height is not None:
        return _resizeimage.resize_cover(image, (width, height))
    if width is not None:
        return _resizeimage.resize_width(image, width)
    if height is not None:
        return _resizeimage.resize_height(image, height)
    raise ValueError('Width and height cannot both be None.')


@pass_context
def filter_negotiate_localizeds(context: Context, localizeds: Iterable[Localized]) -> Localized | None:
    """
    Try to find an object whose locale matches the context's current locale.
    """
    from betty.jinja2 import context_localizer

    return negotiate_localizeds(context_localizer(context).locale, list(localizeds))


@pass_context
def filter_sort_localizeds(context: Context, localizeds: Iterable[Localized], localized_attribute: str, sort_attribute: str) -> Iterable[Localized]:
    """
    Sort localized objects.
    """
    from betty.jinja2 import context_localizer

    get_localized_attr = make_attrgetter(
        context.environment, localized_attribute)
    get_sort_attr = make_attrgetter(context.environment, sort_attribute)

    def _get_sort_key(x: Localized) -> Any:
        return get_sort_attr(negotiate_localizeds(context_localizer(context).locale, get_localized_attr(x)))

    return sorted(localizeds, key=_get_sort_key)


@pass_context
def filter_select_localizeds(context: Context, localizeds: Iterable[Localized], include_unspecified: bool = False) -> Iterable[Localized]:
    """
    Select all objects whose locale matches the context's current locale.

    :param include_unspecified: If True, the return value includes all objects that do not have a locale specified.
    """
    from betty.jinja2 import context_localizer

    for localized in localizeds:
        if include_unspecified and localized.locale in {None, 'mis', 'mul', 'und', 'zxx'}:
            yield localized
        if localized.locale is not None and negotiate_locale(context_localizer(context).locale, [localized.locale]) is not None:
            yield localized


@pass_context
def filter_negotiate_dateds(context: Context, dateds: Iterable[Dated], date: Datey | None) -> Dated | None:
    """
    Try to find an object whose date falls in the given date.

    :param date: A date to select by. If None, then today's date is used.
    """
    with suppress(StopIteration):
        return next(filter_select_dateds(context, dateds, date))
    return None


@pass_context
def filter_select_dateds(context: Context, dateds: Iterable[Dated], date: Datey | None) -> Iterator[Dated]:
    """
    Select all objects whose date falls in the given date.

    :param date: A date to select by. If None, then today's date is used.
    """
    if date is None:
        date = context.resolve_or_missing('today')
    return filter(
        lambda dated: dated.date is None or dated.date.comparable and dated.date in date,
        dateds,
    )


def filter_base64(input: str) -> str:
    """
    Base-64-encode a string.
    """
    return b64encode(input.encode('utf-8')).decode('utf-8')


FILTERS = {
    'base64': filter_base64,
    'camel_case_to_kebab_case': camel_case_to_kebab_case,
    'camel_case_to_snake_case': camel_case_to_snake_case,
    'entity_type_name': get_entity_type_name,
    'file': filter_file,
    'flatten': filter_flatten,
    'format_datey': filter_format_datey,
    'format_degrees': filter_format_degrees,
    'image': filter_image,
    'json': filter_json,
    'locale_get_data': get_data,
    'localize': filter_localize,
    'map': filter_map,
    'minimize': minimize,
    'negotiate_dateds': filter_negotiate_dateds,
    'negotiate_localizeds': filter_negotiate_localizeds,
    'none_void': none_void,
    'paragraphs': filter_paragraphs,
    'select_dateds': filter_select_dateds,
    'select_localizeds': filter_select_localizeds,
    'static_url': filter_static_url,
    'sort_localizeds': filter_sort_localizeds,
    'str': str,
    'unique': filter_unique,
    'upper_camel_case_to_lower_camel_case': upper_camel_case_to_lower_camel_case,
    'url': filter_url,
    'void_none': void_none,
    'walk': filter_walk,
}
