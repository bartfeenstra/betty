"""
Data types with human-readable description texts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typing_extensions import override

from betty.json.linked_data import LinkedDataDumpableJsonLdObject, dump_context
from betty.locale.localizable import StaticTranslationsLocalizable
from betty.privacy import is_public

if TYPE_CHECKING:
    from betty.locale.localizable import Localizable
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


class HasDescription(LinkedDataDumpableJsonLdObject):
    """
    A resource with a description.
    """

    def __init__(
        self,
        *args: Any,
        description: Localizable | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.description = description

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump_context(dump, description="https://schema.org/description")
        if self.description is not None and is_public(self):
            localizers = await project.localizers
            dump["description"] = await StaticTranslationsLocalizable.from_localizable(
                self.description,
                *[
                    await localizers.get(locale)
                    for locale in project.configuration.locales
                ],
            ).dump_linked_data(project)
        return dump
