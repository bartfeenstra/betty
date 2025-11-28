"""
Provide licenses.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar, final

from betty.locale.localizable import _, ngettext
from betty.mutability import Mutable
from betty.plugin import Plugin, PluginTypeDefinition
from betty.plugin.discovery.app import AppDiscovery
from betty.plugin.discovery.entry_point import EntryPointDiscovery
from betty.plugin.discovery.project import ProjectDiscovery
from betty.plugin.human_facing import HumanFacingPluginDefinition

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable


class License(Mutable, Plugin):
    """
    A license.

    Read more about :doc:`/development/plugin/license`.

    To test your own subclasses, use :py:class:`betty.test_utils.license.LicenseTestBase`.
    """

    plugin: ClassVar[LicensePlugin]

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
class LicensePlugin(HumanFacingPluginDefinition[License]):
    """
    A license definition.

    Read more about :doc:`/development/plugin/license`.
    """

    plugin_type_cls = License
    type = PluginTypeDefinition(
        "license",
        _("License"),
        _("Licenses"),
        ngettext("{count} license", "{count} licenses"),
        discoveries=[
            EntryPointDiscovery("betty.license"),
            AppDiscovery(lambda app: app._spdx_license_repository),
            ProjectDiscovery(
                lambda project: project.configuration.licenses.new_plugins()
            ),
        ],
    )
