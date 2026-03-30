"""
CSS resources for HTML pages.
"""

from typing import Any, final, override

from betty.locale.localizable.gettext import _, ngettext
from betty.machine_name import ResolvableMachineName
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import Order, OrderedPluginDefinition
from betty.requirement import Requires
from betty.service.plugin.service import ServicePluginDefinition


class CssResource(Plugin["CssResourceDefinition"]):
    """
    Expose a CSS resource to be included on every HTML page.
    """


@final
@PluginTypeDefinition(
    "css-resource",
    label=_("CSS resource"),
    label_plural=_("CSS resources"),
    label_countable=ngettext("{count} CSS resource", "{count} CSS resources"),
)
class CssResourceDefinition(
    OrderedPluginDefinition[CssResource], ServicePluginDefinition[CssResource]
):
    """
    .. plugin_type:: css-resource.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order | None = None,
        resource: Any,
        auto: bool = False,
        before: Order | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id,
            after=after,
            auto=auto,
            before=before,
            requires=requires,
        )
        self._resource = resource

    @property
    def resource(self) -> Any:
        """
        The URL-generatable resource of the CSS file to include on every HTML page.
        """
        return self._resource


@final
class CssResourceManufacturer(PluginManufacturer[CssResourceDefinition, CssResource]):
    """
    The CSS resource manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[CssResourceDefinition]:
        return CssResourceDefinition
