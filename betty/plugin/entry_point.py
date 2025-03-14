"""
Integrates the plugin API with `distribution packages <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_.
"""

from collections.abc import Sequence
from importlib import metadata
from typing import Generic, TypeVar, final

from betty.json.schema import Schema
from betty.plugin import Plugin
from betty.plugin.lazy import LazyPluginRepositoryBase

_PluginT = TypeVar("_PluginT", bound=Plugin)


@final
class EntryPointPluginRepository(LazyPluginRepositoryBase[_PluginT], Generic[_PluginT]):
    """
    Discover plugins defined as distribution package `entry points <https://packaging.python.org/en/latest/specifications/entry-points/>`_.

    If you are developing a plugin for an existing plugin type that uses entry points, you'll have
    to add that plugin to your package metadata. For example, for a plugin type

    - whose entry point group is ``your-plugin-group``
    - with a plugin class ``MyPlugin`` in the module ``my_package.my_module``
    - and a plugin ID ``my-package-plugin``:

    .. code-block:: toml

        [project.entry-points.'your-plugin-group']
        'my-package-plugin' = 'my_package.my_module:MyPlugin'
    """

    def __init__(
        self, entry_point_group: str, *, schema_template: Schema | None = None
    ):
        super().__init__(schema_template=schema_template)
        self._entry_point_group = entry_point_group

    async def _load_plugins(self) -> Sequence[type[_PluginT]]:
        return [
            entry_point.load()
            for entry_point in metadata.entry_points(
                group=self._entry_point_group,
            )
        ]
