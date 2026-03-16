"""
Tools to build content plugins that render templates.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Mapping, MutableSequence
from typing import TYPE_CHECKING, Any, final, override

from betty.content import Content

if TYPE_CHECKING:
    from betty.document import Document
    from betty.jinja import Environment

type TemplateBuild = (
    str | Iterable[str] | tuple[str | Iterable[str], Mapping[str, Any]] | None
)


class Template(Content):
    """
    Build content by rendering a Jinja2 template.
    """

    def __init__(self, *args: Any, jinja: Environment, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._jinja = jinja

    @final
    @override
    async def build(self, *, document: Document) -> str | None:
        config = await self.build_template(document)
        if config is None:
            return None
        templates: MutableSequence[str]
        if isinstance(config, str):
            templates = [config]
            data = {}
        elif isinstance(config, tuple):
            templates = [config[0]] if isinstance(config[0], str) else config[0]  # ty:ignore[invalid-assignment]
            data = config[1]
        else:
            templates = config  # ty:ignore[invalid-assignment]
            data = {}
        assert templates, "At least one template must be specified"
        rendered_content = (
            await self._jinja.select_template(templates).render_async(
                document=document,
                **data,  # ty:ignore[invalid-argument-type]
            )
        ).strip()
        if rendered_content:
            return rendered_content
        return None

    @abstractmethod
    async def build_template(self, document: Document) -> TemplateBuild:
        """
        Build template data.

        Return a template name, a tuple of a template name and template date to render it. Return ``None`` to prevent
        anything from being rendered at all.
        """
