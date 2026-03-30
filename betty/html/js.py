"""
JavaScript resources for HTML pages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin
from betty.plugin.factory import PluginManufacturer
from betty.plugin.ordered import Order, OrderedPluginClsDefinition
from betty.service.plugin.service import ServicePluginDefinition

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


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
    OrderedPluginClsDefinition[JsResource], ServicePluginDefinition[JsResource]
):
    """
    .. plugin_type:: js-resource.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        after: Order[JsResourceDefinition] = (),
        resource: Any,
        auto: bool = False,
        before: Order[JsResourceDefinition] = (),
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
