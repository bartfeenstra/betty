"""
Provide licenses.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import Plugin, PluginDefinition, PluginTypeDefinition
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable


class License(Plugin["LicenseDefinition"]):
    """
    A license.

    To test your own subclasses, use :py:class:`betty.test_utils.license.LicenseTestBase`.
    """

    @property
    @abstractmethod
    def summary(self) -> Localizable:
        """
        The license summary.
        """

    @property
    @abstractmethod
    def text(self) -> Localizable:
        """
        The full license text.
        """

    @property
    def url(self) -> Localizable | None:
        """
        The URL to an external human-readable resource with more information about this license.
        """
        return None


@final
@PluginTypeDefinition(
    "license",
    base_cls=License,
    label=_("License"),
    label_plural=_("Licenses"),
    label_countable=ngettext("{count} license", "{count} licenses"),
    discovery=[
        EntryPointDiscovery("betty.license"),
        ProjectDiscovery(lambda project: project.configuration.licenses.new_plugins()),
    ],
)
class LicenseDefinition(HumanFacingDefinition, PluginDefinition[License]):
    """
    .. plugin_type:: license.
    """
