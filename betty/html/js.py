"""
JavaScript resources for HTML pages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Self, final

from betty.definition.ordered import Order, OrderedDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition

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
class JsResourceDefinition(OrderedDefinition, PluginDefinition):
    """
    .. plugin_type:: js-resource.
    """

    def __init__(
        self,
        js_resource_id: ResolvableMachineName,
        *,
        after: Order[Self] = (),
        resource: Any,
        auto: bool = False,
        before: Order[Self] = (),
        requires: Requires = (),
    ):
        super().__init__(
            js_resource_id,
            after=after,
            auto=auto,
            before=before,
            requires=requires,
        )
        self.resource: Final[Any] = resource
        """
        The URL-generatable resource of a JS file to include on every HTML page.
        """
