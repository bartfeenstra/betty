"""
Provide licenses.
"""

from abc import abstractmethod

from betty.locale.localizable import Localizable
from betty.mutability import Mutable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class License(Mutable, Plugin):
    """
    A license.

    Read more about :doc:`/development/plugin/license`.

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


LICENSE_REPOSITORY: PluginRepository[License] = EntryPointPluginRepository(
    "betty.license"
)
"""
The license plugin repository.

Read more about :doc:`/development/plugin/license`.
"""
