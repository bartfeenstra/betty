"""
The Betty Sphinx extension.
"""

from __future__ import annotations

from asyncio import run
from collections.abc import Callable, Iterable, MutableSequence, Sequence
from functools import cmp_to_key
from textwrap import indent
from threading import Thread
from typing import TYPE_CHECKING, TypeAlias, TypeVar

from docutils import nodes
from sphinx.util.docutils import SphinxDirective
from sphinx.util.parsing import nested_parse_to_nodes
from typing_extensions import override

from betty.app import App
from betty.config import Configurable, Configuration
from betty.data import Data
from betty.data.aggregate.record import RecordDefinition
from betty.functools import Result
from betty.importlib import import_any
from betty.locale.localize import DEFAULT_LOCALIZER
from betty.plugin import plugin_types
from betty.plugin.dependent import DependentPluginDefinition
from betty.plugin.human_facing import HumanFacingPluginDefinition
from betty.plugin.ordered import OrderedPluginDefinition
from betty.project import Project

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata

    from betty.plugin import PluginDefinition
    from betty.plugin.repository import PluginRepository
    from betty.serde import Serializer

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


def _cmp_formats(left: PluginDefinition, right: PluginDefinition) -> int:
    if left.id == "yaml":
        return -1
    if right.id == "yaml":
        return 1
    return -1 if left.id < right.id else 1


async def _get_serializers() -> Sequence[Serializer]:
    async with (
        App.new_isolated() as app,
        app,
        Project.new_isolated(app) as project,
        project,
    ):
        return [
            await project.new_target(serializer.cls)
            for serializer in sorted(
                await project.plugins("serializer", check_requirements=False),
                key=cmp_to_key(_cmp_formats),
            )
        ]


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
            *self._build_metadata(plugin, plugins),
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

    def _build_metadata(
        self, plugin: PluginDefinition, plugins: PluginRepository[PluginDefinition]
    ) -> list[nodes.Node]:
        cls = plugin.cls
        if issubclass(cls, Configurable):
            configuration_content = f":py:class:`{cls.configuration_cls().__name__} <{cls.configuration_cls().__module__}.{cls.configuration_cls().__qualname__}>`"
        else:
            configuration_content = "*not configurable*"
        content = f"""
.. list-table::
   :widths: 20 10
   :header-rows: 0

   * - Plugin ID
     - ``{plugin.id}``
   * - Class
     - :py:class:`{plugin.cls.__name__} <{plugin.cls.__module__}.{plugin.cls.__qualname__}>`
   * - Configuration
     - {configuration_content}
"""
        if isinstance(plugin, DependentPluginDefinition) and (
            depends_on_content := self._build_other_plugins_references(
                [plugins.get(plugin_id) for plugin_id in plugin.depends_on]
            )
        ):
            content += f"""
   * - Depends on
{depends_on_content}
"""
        if isinstance(plugin, OrderedPluginDefinition):
            if comes_before_content := self._build_other_plugins_references(
                [plugins.get(plugin_id) for plugin_id in plugin.comes_before]
            ):
                content += f"""
   * - Comes before
{comes_before_content}
"""
            if comes_after_content := self._build_other_plugins_references(
                [plugins.get(plugin_id) for plugin_id in plugin.comes_after]
            ):
                content += f"""
   * - Comes after
{comes_after_content}
"""
        return nested_parse_to_nodes(
            self.state,
            content,
            offset=self.content_offset,
        )

    def _build_other_plugins_references(
        self, plugins: Iterable[PluginDefinition]
    ) -> str:
        contents = [
            f":py:class:`{plugin.id} <{plugin.cls.__module__}.{plugin.cls.__qualname__}>`"
            for plugin in sorted(plugins, key=lambda plugin: plugin.id)
        ]
        if not contents:
            return ""
        if len(contents) == 1:
            return f"     - {contents[0]}"
        content = [f"     - * {contents[0]}"]
        for dependency_content in contents[1:]:
            content.append(f"       * {dependency_content}")
        return "\n".join(content)


class _PluginTypeDirective(SphinxDirective):
    required_arguments = 1

    @override
    def run(self) -> list[nodes.Node]:
        # Right-strip periods to avoid D400 and D415 violations.
        plugin_type_id = self.arguments[0].rstrip(".")
        plugin_type = plugin_types[plugin_type_id]
        plugins = _to_thread(lambda: run(_get_plugins(plugin_type_id)))
        return [
            self._build_summary(plugin_type),
            *self._build_metadata(plugin_type),
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

    def _build_metadata(self, plugin_type: type[PluginDefinition]) -> list[nodes.Node]:
        return nested_parse_to_nodes(
            self.state,
            f"""
.. list-table::
   :widths: 20 10
   :header-rows: 0

   * - Plugin type ID
     - ``{plugin_type.type().id}``
   * - Base class
     - :py:class:`{plugin_type.type().base_cls.__name__} <{plugin_type.type().base_cls.__module__}.{plugin_type.type().base_cls.__qualname__}>`
   * - Definition
     - :py:class:`@{plugin_type.__name__}(...) <{plugin_type.__module__}.{plugin_type.__qualname__}>`
""",
            offset=self.content_offset,
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
            f"{plugin.id} (:py:class:`{plugin.cls.__name__} <{plugin.cls.__module__}.{plugin.cls.__qualname__}>`)"
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
                        plugin_types,
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


class _ConfigurationDirective(SphinxDirective):
    required_arguments = 1

    @override
    def run(self) -> list[nodes.Node]:
        # Right-strip periods to avoid D400 and D415 violations.
        cls_name = self.arguments[0].rstrip(".")
        cls = import_any(cls_name)
        assert issubclass(cls, Configuration)
        samples = list(cls.samples())
        if not samples:
            return []
        examples_label = "Examples" if len(samples) > 1 else "Example"
        examples_content = f"""
{examples_label}
{"".join(["=" * len(examples_label)])}

"""
        serializers = _to_thread(lambda: run(_get_serializers()))
        for sample in samples:
            example_content = ""
            if len(samples) > 1:
                example_label = sample.label.localize(DEFAULT_LOCALIZER)
                example_content += f"""
{example_label}
{"".join(["-" * len(example_label)])}
"""
            example_content += """
.. tab-set::

"""
            portable = sample.data.dump()
            for serializer in serializers:
                serialized = serializer.dump(portable)
                example_content += f"""
   .. tab-item:: {serializer.plugin().label.localize(DEFAULT_LOCALIZER)}

      .. code-block:: {serializer.plugin().id}

{indent(serialized, " " * 10)}
"""
            examples_content += example_content
        return nested_parse_to_nodes(
            self.state,
            examples_content,
            offset=self.content_offset,
        )


class _DataDirective(SphinxDirective):
    required_arguments = 1

    @override
    def run(self) -> list[nodes.Node]:
        # Right-strip periods to avoid D400 and D415 violations.
        cls_name = self.arguments[0].rstrip(".")
        cls = import_any(cls_name)
        assert issubclass(cls, Data)
        data = cls.data()
        content = ""

        if isinstance(data, RecordDefinition) and data.fields:
            content += """
Data
====
"""
            for field in sorted(
                data.fields,
                key=lambda field: (not field.required, field.selector.element),
            ):
                primary_label = field.data.label if field.label is None else field.label
                content += f"""
                
``{field.selector.element}`` :sup:`{"required" if field.required else "optional"}`

    **{primary_label.localize(DEFAULT_LOCALIZER)}**
"""
                primary_description = (
                    field.data.description
                    if field.description is None
                    else field.description
                )
                if primary_description is not None:
                    content += f"""
    {primary_description.localize(DEFAULT_LOCALIZER)}
"""
                content += f"""

    Value: :py:class:`{field.data.cls.__name__} <{field.data.cls.__module__}.{field.data.cls.__qualname__}>`
"""
                if field.label is not None:
                    content += f"""
    *{field.data.label.localize(DEFAULT_LOCALIZER)}*
"""
                if field.description is not None and field.data.description is not None:
                    content += f"""
    *{field.data.description.localize(DEFAULT_LOCALIZER)}*
"""

        samples = list(data.samples)
        if samples:
            examples_label = "Examples" if len(samples) > 1 else "Example"
            content += f"""
{examples_label}
{"".join(["=" * len(examples_label)])}

"""
            serializers = _to_thread(lambda: run(_get_serializers()))
            for sample in samples:
                example_content = ""
                if len(samples) > 1:
                    example_label = sample.label.localize(DEFAULT_LOCALIZER)
                    example_content += f"""
{example_label}
{"".join(["-" * len(example_label)])}
"""
                example_content += """
.. tab-set::

"""
                portable = data.dump(sample.data)
                for serializer in serializers:
                    serialized = serializer.dump(portable)
                    example_content += f"""
   .. tab-item:: {serializer.plugin().label.localize(DEFAULT_LOCALIZER)}

      .. code-block:: {serializer.plugin().id}

{indent(serialized, " " * 10)}
"""
                content += example_content

        return nested_parse_to_nodes(
            self.state,
            content,
            offset=self.content_offset,
        )


def setup(app: Sphinx) -> ExtensionMetadata:
    """
    Implement Sphinx's extension setup.
    """
    app.add_directive("configuration", _ConfigurationDirective)
    app.add_directive("data", _DataDirective)
    app.add_directive("plugin", _PluginDirective)
    app.add_directive("plugin_type", _PluginTypeDirective)
    app.add_directive("plugin_types", _PluginTypesDirective)

    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
