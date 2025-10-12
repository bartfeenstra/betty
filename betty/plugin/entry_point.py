"""
Integrates the plugin API with `distribution packages <https://packaging.python.org/en/latest/glossary/#term-Distribution-Package>`_.
"""

from importlib import metadata
from typing import Generic, TypeVar, final

from betty.plugin import PluginDefinition
from betty.plugin.static import StaticPluginRepository

_PluginDefinitionT = TypeVar("_PluginDefinitionT", bound=PluginDefinition)


@final
class EntryPointPluginRepository(
    StaticPluginRepository[_PluginDefinitionT], Generic[_PluginDefinitionT]
):
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
        self,
        plugin: type[_PluginDefinitionT],  # noqa A002
        entry_point_group: str,
        /,
    ):
        super().__init__(
            plugin,
            *(
                entry_point.load()
                for entry_point in metadata.entry_points(
                    group=entry_point_group,
                )
            ),
        )
