"""
The Privacy API.
"""

from __future__ import annotations

import enum
from typing import TYPE_CHECKING, Any, final

from typing_extensions import override

from betty.classtools import Singleton
from betty.json.linked_data import (
    JsonLdObject,
    LinkedDataDumpableWithSchemaJsonLdObject,
)
from betty.json.schema import Boolean

if TYPE_CHECKING:
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class Privacy(enum.Enum):
    """
    The available privacy modes.
    """

    #: The resource is explicitly made public.
    PUBLIC = 1

    #: The resource is explicitly made private.
    PRIVATE = 2

    #: The resource has no explicit privacy. This means that:
    #:
    #: - it may be changed at will
    #: - when checking access, UNDETERMINED evaluates to PUBLIC.
    UNDETERMINED = 3


class HasPrivacy(LinkedDataDumpableWithSchemaJsonLdObject):
    """
    A resource that has privacy.
    """

    def __init__(
        self,
        *args: Any,
        privacy: Privacy | None = None,
        public: bool | None = None,
        private: bool | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if [privacy, public, private].count(None) < 2:
            raise ValueError(
                f"Only one of the `privacy`, `public`, and `private` arguments to {type(self)}.__init__() may be given at a time."
            )
        if privacy is not None:
            self._privacy = privacy
        elif public is True:
            self._privacy = Privacy.PUBLIC
        elif private is True:
            self._privacy = Privacy.PRIVATE
        else:
            self._privacy = Privacy.UNDETERMINED

    @property
    def own_privacy(self) -> Privacy:
        """
        The resource's own privacy.

        This returns the value that was set for :py:attr:`betty.privacy.HasPrivacy.privacy` and ignores
        computed privacies.

        For access control and permissions checking, use :py:attr:`betty.privacy.HasPrivacy.privacy`.
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
    def private(self, private: True) -> None:
        self.privacy = Privacy.PRIVATE

    @property
    def public(self) -> bool:
        """
        Whether this resource is public.
        """
        # Undetermined privacy defaults to public.
        return self.privacy is not Privacy.PRIVATE

    @public.setter
    def public(self, public: True) -> None:
        self.privacy = Privacy.PUBLIC

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["private"] = self.private
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("private", PrivacySchema())
        return schema


@final
class PrivacySchema(Singleton, Boolean):
    """
    A JSON Schema for privacy.
    """

    def __init__(self):
        super().__init__(
            def_name="privacy",
            title="Privacy",
            description="Whether this entity is private (true), or public (false).",
        )


def is_private(target: Any) -> bool:
    """
    Check if the given target is private.
    """
    if isinstance(target, HasPrivacy):
        return target.private
    return False


def is_public(target: Any) -> bool:
    """
    Check if the given target is public.
    """
    if isinstance(target, HasPrivacy):
        return target.public
    return True


def resolve_privacy(privacy: Privacy | HasPrivacy | None) -> Privacy:
    """
    Resolve the privacy of a value.
    """
    if privacy is None:
        return Privacy.UNDETERMINED
    if isinstance(privacy, Privacy):
        return privacy
    return privacy.privacy


def merge_privacies(*privacies: Privacy | HasPrivacy | None) -> Privacy:
    """
    Merge multiple privacies into one.
    """
    privacies = {resolve_privacy(privacy) for privacy in privacies}
    if Privacy.PRIVATE in privacies:
        return Privacy.PRIVATE
    if Privacy.UNDETERMINED in privacies:
        return Privacy.UNDETERMINED
    return Privacy.PUBLIC


def merge_secondary_privacies(
    privacy: Privacy | HasPrivacy | None,
    *secondary_privacies: Privacy | HasPrivacy | None,
) -> Privacy:
    """
    Merge multiple privacies into one.
    """
    privacy = resolve_privacy(privacy)
    if Privacy.PRIVATE in {
        privacy,
        *(resolve_privacy(privacy) for privacy in secondary_privacies),
    }:
        return Privacy.PRIVATE
    return privacy
