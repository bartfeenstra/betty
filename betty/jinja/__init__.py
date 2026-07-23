"""
Provide rendering utilities using `Jinja2 <https://jinja.palletsprojects.com>`_.
"""

from __future__ import annotations

import datetime
from asyncio import to_thread
from collections.abc import Awaitable, Callable, Iterable, Mapping
from os import makedirs
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING, Any, Final, Unpack, cast, final, override

from jinja2 import Environment, FileSystemLoader, pass_context, select_autoescape
from jinja2.async_utils import auto_await
from jinja2.compiler import CodeGenerator, Frame
from jinja2.ext import Extension
from jinja2.nodes import CallBlock, ContextReference, Expr, Node, Template
from jinja2.runtime import Context, DebugUndefined, StrictUndefined
from jinja2.utils import missing
from markupsafe import Markup

from betty import about
from betty.date import Date
from betty.file import read, write
from betty.html.attributes import Attributes, AttributesKwargs
from betty.locale import default_locale, to_language_tag
from betty.localizable import Localizable, ResolvableLocalizable
from betty.localizables.gettext import gettext, ngettext, npgettext, pgettext
from betty.localizables.markup import JoinAnd, JoinOr
from betty.localized import LocalizedStr
from betty.machine_name import MachineName
from betty.media_type import (
    ResolvableMediaType,
    UnsupportedMediaType,
    match_extension,
    resolve_media_type,
)
from betty.media_types.html import HTML
from betty.media_types.jinja import JINJA
from betty.pathlib import resolve_path
from betty.store import StoreItem
from betty.string import kebab_case_to_snake_case
from betty.warnings import deprecate

if TYPE_CHECKING:
    from jinja2.parser import Parser

    from betty.document import Document
    from betty.pathlib import StrPath
    from betty.project import Project


type CopyFunction = Callable[[Path, Path], Awaitable[None]]


def context_document(context: Context) -> Document:
    """
    Get the current document from the Jinja2 context.
    """
    document: Document = context.resolve_or_missing("document")
    if document is missing:
        raise RuntimeError(
            "No `document` context variable exists in this Jinja2 template."
        ) from None
    return document


@final
class _GlobalGettext[*Ts]:
    def __init__(self, factory: Callable[[*Ts], Localizable]):
        self._factory = factory

    def __call__(
        self, *args: *Ts, **format_kwargs: ResolvableLocalizable
    ) -> Localizable:
        localizable = self._factory(*args)
        if format_kwargs:
            return localizable.format(**format_kwargs)
        return localizable


async def new_environment(project: Project, /) -> Environment:
    """
    Create a new environment.
    """
    template_directories = [
        str(path / "templates") for path in project.asset_directories.directories
    ]
    today = datetime.datetime.now(tz=datetime.UTC).date()
    environment = Environment(
        loader=FileSystemLoader(template_directories),
        auto_reload=project.debug,
        enable_async=True,
        undefined=(DebugUndefined if project.debug else StrictUndefined),
        autoescape=select_autoescape(["html.j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
        extensions=[
            "jinja2.ext.do",
            "jinja2.ext.i18n",
            _CacheTagExtension,
        ],
    )
    environment.code_generator_class = _CodeGenerator
    if project.debug:
        environment.add_extension("jinja2.ext.debug")
    environment.globals.update(
        gettext=_GlobalGettext(gettext),  # ty:ignore[invalid-argument-type]
        ngettext=_GlobalGettext(ngettext),  # ty:ignore[invalid-argument-type]
        pgettext=_GlobalGettext(pgettext),  # ty:ignore[invalid-argument-type]
        npgettext=_GlobalGettext(npgettext),  # ty:ignore[invalid-argument-type]
    )
    environment.newstyle_gettext = True  # ty:ignore[unresolved-attribute]
    environment.policies["ext.i18n.trimmed"] = True

    environment.globals.update({
        "about_version_major": about.version_major_label,
        "about_url": about.url,
        "about_url_code": about.url_code,
        "about_url_documentation": about.url_documentation,
        "about_url_report_issue": about.url_report_issue,
        "app": project.upstream,
        "default_locale": default_locale,
        "deprecate": deprecate,
        "localizable_join_and": JoinAnd,
        "localizable_join_or": JoinOr,
        "machine_name": MachineName,
        "new_attributes": _new_html_attributes,
        "project": project,
        "primary_navigation_links": [
            link.link for link in project.links if link.primary
        ],
        "public_css_paths": [resource.resource for resource in project.css_resources],
        "public_js_paths": [resource.resource for resource in project.js_resources],
        "secondary_navigation_links": [
            link.link for link in project.links if not link.primary
        ],
        "tag": _html_tag,
        "today": Date(today.year, today.month, today.day),
    })  # ty:ignore[no-matching-overload]
    environment.filters.update({
        kebab_case_to_snake_case(filter.plugin().id): filter.__call__
        for awaitable_filter in project.jinja_filters
        if (filter := await awaitable_filter)  # noqa: A001
    })
    environment.tests.update({
        kebab_case_to_snake_case(test.plugin().id): test.__call__
        for awaitable_test in project.jinja_tests
        if (test := await awaitable_test)
    })
    return environment


def make_copy_function(
    environment: Environment,
    *,
    document: Document,
    is_localized_and_multilingual: bool | None = None,
    media_types: Iterable[ResolvableMediaType] = (),
    www_directory: StrPath | None = None,
) -> CopyFunction:
    """
    Make a copy function for this renderer that renders supported files.
    """
    media_types = tuple(map(resolve_media_type, media_types))

    async def _copy_function(source: StrPath, destination: StrPath, /) -> None:
        destination = resolve_path(destination)
        await to_thread(makedirs, destination.parent, exist_ok=True)
        try:
            _jinja_media_type, extension = match_extension(source, [JINJA.media_type])
        except UnsupportedMediaType:
            copy2(source, destination)
            return

        destination = destination.with_name(destination.name[: -len(extension)])

        try:
            document_media_type, _extension = match_extension(destination, media_types)
        except UnsupportedMediaType:
            document_media_type = None

        document_resource_url = document.resource_url

        if www_directory:
            try:
                relative_file_destination_path = destination.relative_to(www_directory)
            except ValueError:
                pass
            else:
                resource_parts = relative_file_destination_path.parts
                if not any(
                    resource_part.startswith(".") for resource_part in resource_parts
                ):
                    if is_localized_and_multilingual:
                        resource_parts = resource_parts[1:]
                    document_resource_url = f"betty:///{'/'.join(resource_parts)}"
        content = await read(source)

        template = environment.from_string(content)
        rendered_content = await template.render_async(
            document=document.copy(
                media_type=document_media_type,
                resource=destination,
                resource_url=document_resource_url,
            )
        )
        await write(destination, rendered_content)

    return _copy_function


class _CacheTagExtension(Extension):
    tags: Final[set[str]] = {"cache"}

    @override
    def parse(self, parser: Parser) -> Node | list[Node]:
        lineno = next(parser.stream).lineno
        cache_key = parser.parse_expression()
        body = parser.parse_statements(("name:endcache",), drop_needle=True)
        return CallBlock(
            self.call_method("_cache", [cache_key, ContextReference()]),
            [],
            [],
            body,
        ).set_lineno(lineno)

    async def _cache(
        self, cache_key: str, context: Context, caller: Callable[[], str]
    ) -> str:
        try:
            job_context = context_document(context).context
        except RuntimeError:
            job_context = None
        if job_context is None:
            return await auto_await(caller())
        async with job_context.store.getset(f"jinja2_cache_tag:{cache_key}") as result:
            if isinstance(result, StoreItem):
                return cast(str, await result.value())
            rendered = await auto_await(caller())
            await result(rendered)
            return rendered


@final
class _CodeGenerator(CodeGenerator):
    _character_order_to_html_lang_map: Final[Mapping[str, str]] = {
        "left-to-right": "ltr",
        "right-to-left": "rtl",
    }

    @override
    def visit_Template(self, node: Template, frame: Frame | None = None) -> None:
        self.writeline("from betty.jinja import _CodeGenerator")
        super().visit_Template(node, frame)

    @override
    def _output_child_pre(
        self, node: Expr, frame: Frame, finalize: CodeGenerator._FinalizeInfo
    ) -> None:
        super()._output_child_pre(node, frame, finalize)
        self.write("_CodeGenerator._output_child(context, ")

    @override
    def _output_child_post(
        self, node: Expr, frame: Frame, finalize: CodeGenerator._FinalizeInfo
    ) -> None:
        self.write(")")
        super()._output_child_post(node, frame, finalize)

    @classmethod
    def _output_child(cls, context: Context, value: Any, /) -> Any:
        if isinstance(value, Localizable):
            value = cls._output_localizable(context, value)
        if isinstance(value, LocalizedStr):
            value = cls._output_localized_str(context, value)
        return value

    @classmethod
    def _output_localizable(
        cls, context: Context, value: Localizable, /
    ) -> LocalizedStr:
        return value.localize(context_document(context).localizer)

    @classmethod
    def _output_localized_str(cls, context: Context, value: LocalizedStr, /) -> str:
        output: str = value
        document = context_document(context)
        if document.media_type != HTML:
            return output
        localizer = document.localizer
        if value.locale != localizer.locale:
            localizer_dir = cls._character_order_to_html_lang_map[
                localizer.locale.character_order
            ]
            if value.locale is None:
                has_locale_dir = "auto"
            else:
                has_locale_dir = cls._character_order_to_html_lang_map[
                    value.locale.character_order
                ]
            dir_attribute = (
                f' dir="{has_locale_dir}"' if has_locale_dir != localizer_dir else ""
            )
            output = f'<span lang="{to_language_tag(value.locale)}"{dir_attribute}>{value}</span>'
        # @todo Do we need this?
        if context.eval_ctx.autoescape:
            output = Markup(output)
        return output


@pass_context
def _new_html_attributes(
    context: Context, **attributes: Unpack[AttributesKwargs]
) -> Attributes:
    return Attributes(localizer=context_document(context).localizer).set(**attributes)


@pass_context
def _html_tag(
    context: Context, name: str, body: Any, /, **attributes: Unpack[AttributesKwargs]
) -> str:
    localizer = context_document(context).localizer
    if isinstance(body, Localizable):
        body = body.localize(localizer)
        attributes["html_lang"] = to_language_tag(body.locale)
    return Markup(
        f"<{name}{Attributes(localizer=context_document(context).localizer).set(**attributes)}>{body}</{name}>"
    )
