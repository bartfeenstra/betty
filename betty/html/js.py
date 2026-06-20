"""
JavaScript resources for HTML pages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, final

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import Order, OrderedPluginDefinition

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


@final
@PluginTypeDefinition(
    "js-resource",
    label=_("JavaScript resource"),
    label_plural=_("JavaScript resources"),
    label_countable=ngettext(
        "{count} JavaScript resource", "{count} JavaScript resources"
    ),
)
class JsResourceDefinition(OrderedPluginDefinition):
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
        self.resource: Final[Any] = resource
        """
        The URL-generatable resource of a JS file to include on every HTML page.
        """
