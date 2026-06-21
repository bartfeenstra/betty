"""
Provide licenses.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

from betty.definition.human_facing import HumanFacingDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginTypeDefinition
from betty.plugin.cls import Plugin, PluginClsDefinition
from betty.plugin.factory import PluginManufacturer, PluginManufacturerDefinition

if TYPE_CHECKING:
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


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

    def __init__(
        self,
        plugin_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            plugin_id, label=label, description=description, requires=requires
        )


@final
@PluginManufacturerDefinition(LicenseDefinition)
class LicenseManufacturer(PluginManufacturer[LicenseDefinition, License]):
    """
    The license manufacturer.
    """
