"""
Privacy attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, final, override

from betty.attrs.owner import OwnerAttr
from betty.attrs.proxy import ProxyAttr
from betty.data import DataDefinition
from betty.datas.enum import EnumDefinition
from betty.linked_data import LinkedData, LinkedDataPorter
from betty.localizables.gettext import _
from betty.privacy import Privacy
from betty.prop import HasProps

if TYPE_CHECKING:
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidableType


@final
class PrivacyAttr(
    ProxyAttr["HasPrivacy", Privacy, Privacy, DataDefinition[Privacy]],
    LinkedDataPorter["HasPrivacy"],
):
    """
    An attribute containing a privacy.
    """

    def __init__(self):
        super().__init__(
            proxied=OwnerAttr(EnumDefinition(cls=Privacy, label=_("Privacy")))
        )

    @override
    async def schema(self, project: Project, /) -> VoidableType[PortableMapping]:
        return {
            "$ref": "#/$defs/privacy",
            "$defs": {
                "privacy": {
                    "description": "Whether this entity is private (true), or public (false).",
                    "title": "Privacy",
                    "type": "boolean",
                },
            },
        }

    @override
    async def dump(self, project: Project, data: HasPrivacy, /) -> LinkedData:
        return LinkedData(data.privacy is Privacy.PRIVATE)


class HasPrivacy(HasProps):
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

    @property
    def privacy(self) -> Privacy:
        """
        The resource's privacy.
        """
        return self._get_effective_privacy()

    @privacy.setter
    def privacy(self, privacy: Privacy) -> None:
        self._privacy = privacy

    @privacy.deleter
    def privacy(self) -> None:
        self.privacy = Privacy.UNDETERMINED

    @property
    def private(self) -> bool:
        """
        Whether this resource is private.
        """
        return self.privacy is Privacy.PRIVATE

    @private.setter
    def private(self, private: Literal[True]) -> None:
        self.privacy = Privacy.PRIVATE

    @property
    def public(self) -> bool:
        """
        Whether this resource is public.
        """
        # Undetermined privacy defaults to public.
        return self.privacy is not Privacy.PRIVATE

    @public.setter
    def public(self, public: Literal[True]) -> None:
        self.privacy = Privacy.PUBLIC
