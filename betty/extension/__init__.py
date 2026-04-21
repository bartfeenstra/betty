"""Provide Betty's extension API."""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer
from betty.service.plugin import PluginServiceProvider
from betty.service_level import ServiceLevel

if TYPE_CHECKING:
    from betty.locale.localizable import ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires
    from betty.typing import Intersection as Intersection


class Extension[ServiceLevelT: ServiceLevel](
    PluginServiceProvider[ServiceLevelT], Plugin["ExtensionDefinition"]
):
    """
    Integrate custom services with a :py:class:`service level <betty.service_level.ServiceLevel>`.
    """


@final
@PluginTypeDefinition(
    "extension",
    label=_("Extension"),
    label_plural=_("Extensions"),
    label_countable=ngettext("{count} extension", "{count} extensions"),
)
class ExtensionDefinition(HumanFacingDefinition, PluginClsDefinition[Extension]):
    """
    .. plugin_type:: extension.

    Betty's functionality can be altered using *extensions*. An extension can do many things, such as loading new or
    expanding existing ancestry data, or generating additional content for your site.

    Some extensions are configurable. That means that other than enabling them, you can set the configuration options
    that determine how the extension should work. This can be done in your project's
    :py:class:`configuration <betty.project.data.ProjectConfiguration>`.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id, label=label, description=description, requires=requires
        )


@final
class ExtensionManufacturer(PluginManufacturer[ExtensionDefinition, Extension]):
    """
    The extension manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[ExtensionDefinition]:
        return ExtensionDefinition
