"""
JavaScript resources for HTML pages.
"""

from typing import Any, final, override

from betty.locale.localizable.gettext import _, ngettext
from betty.machine_name import ResolvableMachineName
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import Order, OrderedPluginDefinition
from betty.requirement import Requires
from betty.service.plugin import ServicePluginDefinition


class JsResource(Plugin["JsResourceDefinition"]):
    """
    Expose a JavaScript resource to be included on every HTML page.
    """


@final
@PluginTypeDefinition(
    "js-resource",
    label=_("JavaScript resource"),
    label_plural=_("JavaScript resources"),
    label_countable=ngettext(
        "{count} JavaScript resource", "{count} JavaScript resources"
    ),
)
class JsResourceDefinition(
    OrderedPluginDefinition[JsResource], ServicePluginDefinition[JsResource]
):
    """
    .. plugin_type:: js-resource.
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
        The URL-generatable resource of a JS file to include on every HTML page.
        """
        return self._resource


@final
class JsResourceManufacturer(PluginManufacturer[JsResourceDefinition, JsResource]):
    """
    The JavaScript resource manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[JsResourceDefinition]:
        return JsResourceDefinition
