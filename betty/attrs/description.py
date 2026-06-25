"""
Data that has human-readable descriptions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attrs.localizable import new_localizable_attr
from betty.attrs.privacy import HasPrivacy
from betty.json_schemas.static_translations import new_static_translations_schema
from betty.linked_data import HasLinkedDataAttrs, LinkedData
from betty.localizable.linked_data import dump_linked_data
from betty.localizables.gettext import _
from betty.prop import HasProps
from betty.typing import Voidable, VoidableType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidType


class HasDescription(HasLinkedDataAttrs, HasProps):
    """
    Data with a description.
    """

    description = new_localizable_attr(label=_("Description")).optional
    """
    The description.
    """

    def __init__(
        self,
        *args: Any,
        description: ResolvableLocalizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.description = description

    @override
    @classmethod
    async def linked_data_schema_properties(
        cls, project: Project, /
    ) -> Mapping[str, VoidableType[PortableMapping]]:
        return {
            "description": Voidable(new_static_translations_schema()),
        }

    @override
    async def dump_linked_data_properties(
        self, project: Project, /
    ) -> Mapping[str, LinkedData | VoidType]:
        if self.description is not None and (
            not isinstance(self, HasPrivacy) or self.public
        ):
            return {
                "description": LinkedData(
                    dump_linked_data(
                        self.description, localizers=await project.public_localizers
                    ),
                    "https://schema.org/description",
                ),
            }
        return {}
