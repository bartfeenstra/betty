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
    Data that has privacy.
    """

    privacy = PrivacyAttr()
    """
    The data's privacy.
    """

    def __init__(
        self, *args: Any, privacy: Privacy = Privacy.UNDETERMINED, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.privacy = privacy
