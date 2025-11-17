"""
Provide licenses.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, ClassVar, final

from betty.locale.localizable import _
from betty.mutability import Mutable
from betty.plugin import (
    ClassedPlugin,
    ClassedPluginDefinition,
    HumanFacingPluginDefinition,
    PluginTypeDefinition,
    ProjectPluginRepositoryDefinition,
)

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable


class License(Mutable, ClassedPlugin):
    """
    A license.

    Read more about :doc:`/development/plugin/license`.

    To test your own subclasses, use :py:class:`betty.test_utils.license.LicenseTestBase`.
    """

    plugin: ClassVar[LicenseDefinition]

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
class LicenseDefinition(HumanFacingPluginDefinition, ClassedPluginDefinition[License]):
    """
    A license definition.

    Read more about :doc:`/development/plugin/license`.
    """

    plugin_type_cls = License
    type = PluginTypeDefinition(
        id="license",
        label=_("License"),
        repository=ProjectPluginRepositoryDefinition(
            lambda project: project.license_repository
        ),
    )
