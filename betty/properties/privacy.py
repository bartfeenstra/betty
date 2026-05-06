"""
Privacy properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, final, override

from betty.datas.enum import EnumDefinition
from betty.linked_data import LinkedDataDumper
from betty.locale.localizable.gettext import _
from betty.privacy import Privacy
from betty.privacy.schema import PrivacySchema
from betty.property import AttrProperty

if TYPE_CHECKING:
    from betty.project import Project


@final
class PrivacyProperty(AttrProperty, LinkedDataDumper[object, PrivacySchema, bool]):
    """
    A property containing a privacy.
    """

    def __init__(self):
        super().__init__(EnumDefinition(Privacy, label=_("Privacy")))

    @override
    async def linked_data_schema_for(self, project: Project, /) -> PrivacySchema:
        return PrivacySchema()

    @override
    async def dump_linked_data_for(self, project: Project, target: object, /) -> bool:
        if isinstance(target, HasPrivacy):
            privacy = target.privacy
        else:
            privacy = getattr(target, self._attr_name)
        return privacy is Privacy.PRIVATE


class HasPrivacy:
    """
    A resource that has privacy.
    """

    _privacy = PrivacyProperty()

    def __init__(
        self, *args: Any, privacy: Privacy = Privacy.UNDETERMINED, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self._privacy = privacy

    @property
    def own_privacy(self) -> Privacy:
        """
        The resource's own privacy.

        This returns the value that was set for :py:attr:`betty.properties.privacy.HasPrivacy.privacy` and ignores
        computed privacies.

        For access control and permissions checking, use :py:attr:`betty.properties.privacy.HasPrivacy.privacy`.
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
