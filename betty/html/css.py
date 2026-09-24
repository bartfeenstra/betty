"""
CSS resources for HTML pages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Final, Self, final

from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.ordered import Order, OrderedPluginDefinition

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


@final
@PluginTypeDefinition(
    "css-resource",
    label=_("CSS resource"),
    label_plural=_("CSS resources"),
    label_countable=ngettext("{count} CSS resource", "{count} CSS resources"),
)
class CssResourceDefinition(OrderedPluginDefinition):
    """
    .. plugin_type:: css-resource.
    """

    def __init__(
        self,
        css_resource_id: ResolvableMachineName,
        *,
        after: Order[Self] = (),
        resource: Any,
        auto: bool = False,
        before: Order[Self] = (),
        requires: Requires = (),
    ):
        super().__init__(
            css_resource_id,
            after=after,
            auto=auto,
            before=before,
            requires=requires,
        )
        self.resource: Final[Any] = resource
        """
        The URL-generatable resource of the CSS file to include on every HTML page.
        """
