"""
The Betty Sphinx extension.
"""

from __future__ import annotations

from asyncio import run
from collections.abc import Callable, Iterable, MutableSequence
from threading import Thread
from typing import TYPE_CHECKING, TypeAlias, TypeVar

from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from typing_extensions import override

from betty.app import App
from betty.config import Configurable
from betty.functools import Result
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin import plugin_types
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.project import Project

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata

    from betty.plugin import PluginDefinition
    from betty.plugin.repository import PluginRepository


_T = TypeVar("_T")
NodesLike: TypeAlias = nodes.Node | Iterable[nodes.Node] | None


def _to_thread(target: Callable[[], _T]) -> _T:
    result = Result(target)
    thread = Thread(target=result)
    thread.start()
    thread.join()
    return result.result()


async def _get_plugins(plugin_type_id: str) -> PluginRepository:
    async with (
        App.new_isolated() as app,
        app,
        Project.new_isolated(app) as project,
        project,
    ):
        return await project.plugins(plugin_type_id, check_requirements=False)


def _build_definition_list(
    definitions_nodes: Iterable[tuple[NodesLike, NodesLike]],
) -> nodes.Node:
    return nodes.definition_list(
        "",
        *[
            nodes.definition_list_item(
                "",
                nodes.term("", "", *_ensure_nodes(term_nodes)),
                nodes.definition("", *_ensure_nodes(definition_nodes)),
            )
            for term_nodes, definition_nodes in definitions_nodes
        ],
    )


def _ensure_nodes(nodes_like: NodesLike) -> Iterable[nodes.Node]:
    if nodes_like is None:
        return []
    if isinstance(nodes_like, nodes.Node):
        return [nodes_like]
    return nodes_like


class _PluginDirective(SphinxDirective):
    required_arguments = 1

    @override
    def run(self) -> list[nodes.Node]:
        # Right-strip periods to avoid D400 and D415 violations.
        argument = self.arguments[0].rstrip(".")
        try:
            plugin_type_id, plugin_id = argument.split(":")
        except ValueError:
            raise ValueError(
                f"The plugin directive requires a single argument that is a plugin type ID and a plugin ID, joined with a colon (:), but `{argument}` was given."
            ) from None
        plugins = _to_thread(lambda: run(_get_plugins(plugin_type_id)))
        plugin = plugins[plugin_id]
        return [
            self._build_summary(plugin),
            self._build_metadata(plugin),
        ]

    def _build_summary(self, plugin: PluginDefinition) -> nodes.Node:
        summary_nodes, _ = self.parse_inline(
            f"The ``{plugin.id}`` :py:class:`{plugin.type().label.localize(DEFAULT_LOCALIZER).lower()} <{type(plugin).__module__}.{type(plugin).__qualname__}>` plugin."
        )
        if isinstance(plugin, HumanFacingPluginDefinition):
            description = plugin.description
            if description:
                summary_nodes.append(nodes.Text(" "))
                summary_nodes.append(
                    nodes.Text(description.localize(DEFAULT_LOCALIZER))
                )
        return nodes.paragraph("", "", *summary_nodes)

    def _build_metadata(self, plugin: PluginDefinition) -> nodes.Node:
        cls_nodes = self.parse_text_to_nodes(
            f":py:class:`{type(plugin).__module__}.{type(plugin).__qualname__}`"
        )
        definitions_nodes = [
            (
                nodes.Text("Plugin ID"),
                nodes.literal(text=plugin.id),
            ),
            (
                nodes.Text("Class"),
                cls_nodes,
            ),
        ]
        cls = plugin.cls
        if issubclass(cls, Configurable):
            configuration_cls_nodes = self.parse_text_to_nodes(
                f":py:class:`{cls.configuration_cls().__module__}.{cls.configuration_cls().__qualname__}`"
            )
            definitions_nodes.append(
                (
                    nodes.Text("Configuration"),
                    configuration_cls_nodes,
                )
            )
        return _build_definition_list(definitions_nodes)


class _PluginTypeDirective(SphinxDirective):
    required_arguments = 1

    @override
    def run(self) -> list[nodes.Node]:
        # Right-strip periods to avoid D400 and D415 violations.
        plugin_type_id = self.arguments[0].rstrip(".")
        plugin_type = plugin_types()[plugin_type_id]
        plugins = _to_thread(lambda: run(_get_plugins(plugin_type_id)))
        return [
            self._build_summary(plugin_type),
            self._build_metadata(plugin_type),
            *self._build_builtin_plugins(plugin_type, plugins),
        ]

    def _build_summary(self, plugin_type: type[PluginDefinition]) -> nodes.Node:
        summary_node = nodes.paragraph(
            "",
            "",
            nodes.Text(
                f"The {plugin_type.type().label.localize(DEFAULT_LOCALIZER).lower()} plugin type."
            ),
        )
        description = plugin_type.type().description
        if description:
            summary_node.append(nodes.Text(" "))
            summary_node.append(nodes.Text(description.localize(DEFAULT_LOCALIZER)))
        return summary_node

    def _build_metadata(self, plugin_type: type[PluginDefinition]) -> nodes.Node:
        base_cls_nodes = self.parse_text_to_nodes(
            f":py:class:`{plugin_type.type().base_cls.__module__}.{plugin_type.type().base_cls.__qualname__}`"
        )
        return _build_definition_list(
            [
                (
                    nodes.Text("Plugin type ID"),
                    nodes.literal(text=plugin_type.type().id),
                ),
                (
                    nodes.Text("Base class"),
                    base_cls_nodes,
                ),
            ]
        )

    def _build_builtin_plugins(
        self, plugin_type: type[PluginDefinition], plugins: PluginRepository
    ) -> list[nodes.Node]:
        return [
            nodes.paragraph(
                "",
                "",
                nodes.Text(
                    f"Built-in {plugin_type.type().label_plural.localize(DEFAULT_LOCALIZER).lower()}:"
                ),
            ),
            _build_definition_list(
                [
                    self._build_builtin_plugin_definition(plugin)
                    for plugin in sorted(plugins, key=lambda plugin: plugin.id)
                ]
            ),
        ]

    def _build_builtin_plugin_definition(
        self, plugin: PluginDefinition
    ) -> tuple[NodesLike, NodesLike]:
        term_nodes, _ = self.parse_inline(
            f"{plugin.id} (:py:class:`{plugin.cls.__module__}.{plugin.cls.__qualname__}`)"
        )
        definition_nodes: MutableSequence[nodes.Node] | None = None
        if isinstance(plugin, HumanFacingPluginDefinition):
            definition_nodes = [nodes.Text(plugin.label.localize(DEFAULT_LOCALIZER))]
            if plugin.description:
                definition_nodes.append(
                    nodes.Text(f": {plugin.description.localize(DEFAULT_LOCALIZER)}")
                )
        return term_nodes, definition_nodes


class _PluginTypesDirective(SphinxDirective):
    @override
    def run(self) -> list[nodes.Node]:
        return [
            _build_definition_list(
                [
                    self._build_builtin_plugin_type_definition(plugin_type)
                    for plugin_type in sorted(
                        plugin_types().values(),
                        key=lambda plugin_type: plugin_type.type().label.localize(
                            DEFAULT_LOCALIZER
                        ),
                    )
                ]
            ),
        ]

    def _build_builtin_plugin_type_definition(
        self, plugin_type: type[PluginDefinition]
    ) -> tuple[NodesLike, NodesLike]:
        term_nodes, _ = self.parse_inline(
            f":py:class:`{plugin_type.type().label.localize(DEFAULT_LOCALIZER)} <{plugin_type.__module__}.{plugin_type.__qualname__}>` (``{plugin_type.type().id}``)"
        )
        description = plugin_type.type().description
        if description:
            return term_nodes, nodes.Text(description.localize(DEFAULT_LOCALIZER))
        return term_nodes, None


def setup(app: Sphinx) -> ExtensionMetadata:
    """
    Implement Sphinx's extension setup.
    """
    app.add_directive("plugin", _PluginDirective)
    app.add_directive("plugin_type", _PluginTypeDirective)
    app.add_directive("plugin_types", _PluginTypesDirective)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
