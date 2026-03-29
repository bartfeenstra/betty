"""
The Jinja filter API.
"""

from __future__ import annotations

from typing import final, override

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer
from betty.plugin.service import ServicePluginDefinition


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
class JinjaFilterDefinition(ServicePluginDefinition[JinjaFilter]):
    """
    .. plugin_type:: jinja-filter.
    """


@final
class JinjaFilterManufacturer(PluginManufacturer[JinjaFilterDefinition, JinjaFilter]):
    """
    The Jinja filter manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[JinjaFilterDefinition]:
        return JinjaFilterDefinition
