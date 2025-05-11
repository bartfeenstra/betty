"""
Provide licenses.
"""

from abc import abstractmethod
from typing import final

from typing_extensions import override

from betty.locale.localizable import Localizable, _
from betty.machine_name import MachineName
from betty.mutability import Mutable
from betty.plugin import Plugin, PluginRepository
from betty.plugin.entry_point import EntryPointPluginRepository


class License(Mutable, Plugin):
    """
    A license.

    Read more about :doc:`/development/plugin/license`.

    To test your own subclasses, use :py:class:`betty.test_utils.license.LicenseTestBase`.
    """

    @final
    @override
    @classmethod
    def plugin_type_cls(cls) -> type[Plugin]:
        return License

    @final
    @override
    @classmethod
    def plugin_type_id(cls) -> MachineName:
        return "license"

    @final
    @override
    @classmethod
    def plugin_type_label(cls) -> Localizable:
        return _("License")

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
    License, "betty.license"
)
"""
The license plugin repository.

Read more about :doc:`/development/plugin/license`.
"""
