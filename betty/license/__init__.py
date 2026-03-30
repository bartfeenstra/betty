"""
Provide licenses.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final, override

from betty.definition.human_facing import HumanFacingDefinition
from betty.locale.localizable.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer

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
    label=_("License"),
    label_plural=_("Licenses"),
    label_countable=ngettext("{count} license", "{count} licenses"),
)
class LicenseDefinition(HumanFacingDefinition, PluginClsDefinition[License]):
    """
    .. plugin_type:: license.
    """


@final
class LicenseManufacturer(PluginManufacturer[LicenseDefinition, License]):
    """
    The license manufacturer.
    """

    @override
    @classmethod
    def plugin_type(cls) -> type[LicenseDefinition]:
        return LicenseDefinition
