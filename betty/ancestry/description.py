"""
Data types with human-readable description texts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.json.linked_data import LinkedDataDumpableJsonLdObject, dump_context
from betty.locale.localizable import (
    OptionalStaticTranslationsLocalizableAttr,
    ShorthandStaticTranslations,
)

if TYPE_CHECKING:
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class HasDescription(LinkedDataDumpableJsonLdObject):
    """
    A resource with a description.
    """

    #: The human-readable description.
    description = OptionalStaticTranslationsLocalizableAttr(
        "description", title="Description"
    )

    def __init__(
        self,
        *args: Any,
        description: ShorthandStaticTranslations | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        if description is not None:
            self.description.replace(description)

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(dump, description="https://schema.org/description")
        return dump
