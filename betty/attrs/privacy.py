"""
Privacy attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, final, override

from betty.attrs.owner import OwnerAttr
from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.enum import EnumDefinition
from betty.json_schemas.privacy import PrivacySchema
from betty.linked_data import LinkedDataDumper
from betty.localizables.gettext import _
from betty.privacy import HasPrivacy as HasPrivacyPrivacy
from betty.privacy import Privacy
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.project import Project


@final
class PrivacyAttr(
    ProxyAttr["HasPrivacy", Privacy, Privacy, DataDefinition[Privacy]],
    LinkedDataDumper["HasPrivacy", PrivacySchema, bool],
):
    """
    An attribute containing a privacy.
    """

    def __init__(self):
        super().__init__(
            proxied=OwnerAttr(EnumDefinition(cls=Privacy, label=_("Privacy")))
        )

    @override
    async def linked_data_schema_for(self, project: Project, /) -> PrivacySchema:
        return PrivacySchema()

    @override
    async def dump_linked_data_for(
        self, project: Project, target: HasPrivacy, /
    ) -> bool:
        return target.privacy is Privacy.PRIVATE


class HasPrivacy(HasPrivacyPrivacy, HasProps):
    """
    A resource that has privacy.
    """

    _privacy = PrivacyAttr()

    def __init__(
        self, *args: Any, privacy: Privacy = Privacy.UNDETERMINED, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self._privacy = privacy

    @property
    def own_privacy(self) -> Privacy:
        """
        The resource's own privacy.

        This returns the value that was set for :py:attr:`betty.attrs.privacy.HasPrivacy.privacy` and ignores
        computed privacies.

        For access control and permissions checking, use :py:attr:`betty.attrs.privacy.HasPrivacy.privacy`.
        """
        return self._privacy

    def _get_effective_privacy(self) -> Privacy:
        return self.own_privacy

    @override
    @property
    def privacy(self) -> Privacy:
        return self._get_effective_privacy()

    @privacy.setter
    def privacy(self, privacy: Privacy) -> None:
        self._privacy = privacy

    @privacy.deleter
    def privacy(self) -> None:
        self.privacy = Privacy.UNDETERMINED
