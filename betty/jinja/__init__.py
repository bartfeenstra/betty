"""
Provide rendering utilities using `Jinja2 <https://jinja.palletsprojects.com>`_.
"""

from __future__ import annotations

import datetime
from asyncio import to_thread
from collections.abc import Callable, Iterable, Mapping
from shutil import copy2
from typing import TYPE_CHECKING, Any, cast, final, override
from warnings import warn

from jinja2 import (
    Environment,
    FileSystemLoader,
    UndefinedError,
    pass_context,
    select_autoescape,
)
from jinja2.async_utils import auto_await
from jinja2.ext import Extension
from jinja2.nodes import CallBlock, ContextReference, Node
from jinja2.runtime import Context as JinjaContext
from jinja2.runtime import DebugUndefined, StrictUndefined
from jinja2.utils import missing

from betty import about
from betty.content_type import ContentTypeDefinition, ContentTypeRepository
from betty.date import Date
from betty.file import CopyFunction, read, write
from betty.html.attributes import Attributes
from betty.importlib import fully_qualified_name
from betty.locale import default_locale
from betty.localizables.markup import JoinAnd, JoinOr
from betty.machine_name import MachineName
from betty.pathlib import resolve_path
from betty.store import StoreItem
from betty.string import kebab_case_to_snake_case
from betty.warnings import deprecate

if TYPE_CHECKING:
    from jinja2.parser import Parser
    from ty_extensions import Intersection

    from betty.classtools.class_var import HasClassVars
    from betty.data import Data
    from betty.datas.aggregate.record.object import ObjectDefinition
    from betty.document import Document
    from betty.pathlib import StrPath
    from betty.project import Project

type TemplateNames = tuple[str, ...]
type ResolvableTemplateNames = str | Iterable[str] | TemplateNames
type TemplateData = Mapping[str, Any]


def resolve_template_names(names: ResolvableTemplateNames, /) -> TemplateNames:
    """
    Resolve template names.
    """
    if isinstance(names, str):
        return tuple({names})
    return tuple(names)


def context_document(context: JinjaContext) -> Document:
    """
    Get the current document from the Jinja2 context.
    """
    document: Document = context.resolve_or_missing("document")
    if document is missing:
        raise RuntimeError(
            "No `document` context variable exists in this Jinja2 template."
        ) from None
    return document


async def new_environment(project: Project, /) -> Environment:
    """
    Create a new environment.
    """
    template_directories = [
        str(path / "templates") for path in project.assets.directories
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
    if project.debug:
        environment.add_extension("jinja2.ext.debug")
    environment.install_gettext_callables(  # ty:ignore[unresolved-attribute]
        gettext=_gettext,
        ngettext=_ngettext,
        pgettext=_pgettext,
        npgettext=_npgettext,
        newstyle=True,
    )
    environment.policies["ext.i18n.trimmed"] = True

    environment.globals.update({
        "about_version_major": about.version_major_label,
        "about_url": about.url,
        "about_url_code": about.url_code,
        "about_url_documentation": about.url_documentation,
        "about_url_report_issue": about.url_report_issue,
        "default_locale": default_locale,
        "deprecate": deprecate,
        "localizable_join_and": JoinAnd,
        "localizable_join_or": JoinOr,
        "machine_name": MachineName,
        "new_attributes": Attributes,
        "project": _ObjectProxy(
            project,
            "localizers",
            "plugins",
            "renderer",
            "service_providers",
            "url_generator",
        ),
        "primary_navigation_links": [
            link.link for link in project.links if link.primary
        ],
        "public_css_paths": [resource.resource for resource in project.css_resources],
        "public_js_paths": [resource.resource for resource in project.js_resources],
        "secondary_navigation_links": [
            link.link for link in project.links if not link.primary
        ],
        "today": Date(today.year, today.month, today.day),
    })  # ty:ignore[no-matching-overload]
    environment.filters.update({
        kebab_case_to_snake_case(filter.definition.id): filter.__call__
        for awaitable_filter in project.jinja_filters
        if (filter := await awaitable_filter)  # noqa: A001
    })
    environment.tests.update({
        kebab_case_to_snake_case(test.definition.id): test.__call__
        for awaitable_test in project.jinja_tests
        if (test := await awaitable_test)
    })
    return environment


@pass_context
def _gettext(context: JinjaContext, message: str) -> str:
    return context_document(context).localizer.translate.gettext(message)


@pass_context
def _ngettext(
    context: JinjaContext, message_singular: str, message_plural: str, n: int
) -> str:
    return context_document(context).localizer.translate.ngettext(
        message_singular, message_plural, n
    )


@pass_context
def _pgettext(context: JinjaContext, gettext_context: str, message: str) -> str:
    return context_document(context).localizer.translate.pgettext(
        gettext_context, message
    )


@pass_context
def _npgettext(
    context: JinjaContext,
    gettext_context: str,
    message_singular: str,
    message_plural: str,
    n: int,
) -> str:
    return context_document(context).localizer.translate.npgettext(
        gettext_context, message_singular, message_plural, n
    )


def make_copy_function(
    environment: Environment,
    /,
    *,
    document: Document,
    is_localized_and_multilingual: bool | None = None,
    media_types: Iterable[ContentTypeDefinition],
    www_directory: StrPath | None = None,
) -> CopyFunction:
    """
    Make a copy function for this renderer that renders supported files.
    """
    media_types = ContentTypeRepository(*media_types)
    parents = set()

    async def _copy_function(source: StrPath, destination: StrPath, /) -> None:
        destination = resolve_path(destination)
        if destination.parent not in parents:
            await to_thread(destination.parent.mkdir, exist_ok=True, parents=True)
            parents.add(destination.parent)

        if not str(source).endswith(".j2"):
            copy2(source, destination)
            return

        destination = destination.with_name(destination.name[:-3])

        document_media_type, _extension = media_types.extensions.require(destination)

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
                content_type=document_media_type,
                resource=destination,
                resource_url=document_resource_url,
            )
        )
        await write(destination, rendered_content)

    return _copy_function


class _CacheTagExtension(Extension):
    tags = {"cache"}  # noqa: RUF012

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
        self, cache_key: str, context: JinjaContext, caller: Callable[[], str]
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
class _ObjectProxy:
    """
    A proxy around defined data objects.

    This restricts access to those attributes (fields) from the object's definition or any :py:class:`betty.attr.Attr`.
    """

    __slots__ = ("__wrapped__", "_attrs", "_deprecated")

    def __init__(
        self,
        wrapped: Intersection[Data[ObjectDefinition], HasClassVars],
        *deprecated: str,
    ):
        self.__wrapped__ = wrapped
        self._attrs = {attr.operator for attr in wrapped.definition.fields}
        self._deprecated = set(deprecated)

    def __getattr__(self, attr: str, /) -> Any:
        if attr in self._attrs:
            return getattr(self.__wrapped__, attr)
        if attr in self._deprecated:
            warn(
                f"{fully_qualified_name(self.__wrapped__)}.{attr} is not a defined data attribute, and should not be accessed in templates.",
                DeprecationWarning,
                stacklevel=2,
            )
            return getattr(self.__wrapped__, attr)
        raise UndefinedError(
            f"{fully_qualified_name(self.__wrapped__)}.{attr} is not a defined data attribute, and cannot be accessed in templates. Do you mean {', '.join(sorted(self._attrs))} ?"
        )
