"""
Provide licenses.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.definition.cls import ClsDefinition
from betty.localizables.gettext import _, ngettext
from betty.plugin import PluginDefinition, PluginTypeDefinition
from betty.plugin.cls.factory import PluginManufacturerDefinition
from betty.plugin.data.factory import NewDataPlugin

if TYPE_CHECKING:
    from betty.localizable import Localizable, ResolvableLocalizable
    from betty.machine_name import ResolvableMachineName
    from betty.requirement import Requires


class License(Object["LicenseDefinition"]):
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
class LicenseDefinition(
    ClsDefinition[License], PluginDefinition, ObjectDefinition[License]
):
    """
    .. plugin_type:: license.
    """

    def __init__(
        self,
        license_id: ResolvableMachineName,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
        requires: Requires = (),
    ):
        super().__init__(
            license_id, label=label, description=description, requires=requires
        )


@final
@PluginManufacturerDefinition(LicenseDefinition)
class NewLicense(NewDataPlugin):
    """
    Create new licenses from portable data.
    """
