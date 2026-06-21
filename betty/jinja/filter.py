"""
The Jinja filter API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition

if TYPE_CHECKING:
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class JinjaFilter(Plugin["JinjaFilterDefinition"]):
    """
    A Jinja filter.

    Subclasses **MUST** have a ``.__call__()`` method of any signature.
    """


@final
@PluginTypeDefinition(
    "jinja-filter",
    label=_("Jinja filter"),
    label_plural=_("Jinja filters"),
    label_countable=ngettext("{count} Jinja filter", "{count} Jinja filters"),
)
class JinjaFilterDefinition(PluginClsDefinition[JinjaFilter]):
    """
    .. plugin_type:: jinja-filter.
    """

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        auto: bool = False,
        requires: Requires = (),
    ):
        super().__init__(plugin_id, auto=auto, requires=requires)


@final
@PluginManufacturerDefinition(JinjaFilterDefinition)
class JinjaFilterManufacturer(PluginManufacturer[JinjaFilterDefinition, JinjaFilter]):
    """
    The Jinja filter manufacturer.
    """
