"""
The Jinja test API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer
from betty.service.plugin import ServicePluginDefinition

if TYPE_CHECKING:
    import builtins


class JinjaTest(Plugin["JinjaTestDefinition"]):
    """
    A Jinja test.
    """


@final
@PluginTypeDefinition(
    "jinja-test",
    label=_("Jinja test"),
    label_plural=_("Jinja tests"),
    label_countable=ngettext("{count} Jinja test", "{count} Jinja tests"),
)
class JinjaTestDefinition(ServicePluginDefinition[JinjaTest]):
    """
    .. plugin_type:: jinja-test.
    """


@final
class JinjaTestManufacturer(PluginManufacturer[JinjaTestDefinition, JinjaTest]):
    """
    The Jinja test manufacturer.
    """

    @override
    @classmethod
    def type(cls) -> builtins.type[JinjaTestDefinition]:
        return JinjaTestDefinition
