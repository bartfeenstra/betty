"""
Provide copyrights.
"""

from abc import abstractmethod

from betty.locale.localizable import Localizable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class Copyright(Plugin):
    """
    A copyright.

    Read more about :doc:`/development/plugin/copyright`.

    To test your own subclasses, use :py:class:`betty.test_utils.copyright.CopyrightTestBase`.
    """

    @property
    @abstractmethod
    def summary(self) -> Localizable:
        """
        The copyright summary.
        """
        pass

    @property
    @abstractmethod
    def text(self) -> Localizable:
        """
        The full copyright text.
        """
        pass


COPYRIGHT_REPOSITORY: PluginRepository[Copyright] = EntryPointPluginRepository(
    "betty.copyright"
)
"""
The copyright plugin repository.

Read more about :doc:`/development/plugin/copyright`.
"""
