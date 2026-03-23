"""
The Jinja test API.
"""

from __future__ import annotations

from abc import ABC
from typing import final, override

from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.factory import PluginManufacturer
from betty.service.plugin import ServicePluginDefinition


class JinjaTest(Plugin["JinjaTestDefinition"], ABC):
    """
    A Jinja test.

    Subclasses **MUST** have a synchronous ``__call__()`` method that returns a boolean, and takes one or more arguments.
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
    def plugin_type(cls) -> type[JinjaTestDefinition]:
        return JinjaTestDefinition
