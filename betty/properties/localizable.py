"""
Localizable properties.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.datas.localizable import LocalizableDefinition
from betty.linked_data import LinkedDataDumper
from betty.locale import to_language_tag
from betty.locale.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)
from betty.locale.localizable.static import (
    STATIC_TRANSLATIONS_SCHEMA,
    StaticTranslations,
)
from betty.property import Property

if TYPE_CHECKING:
    from betty.json_schema import Schema
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class LocalizableProperty(
    Property[Localizable, ResolvableLocalizable], LinkedDataDumper[Localizable]
):
    """
    A property containing a :py:class:`betty.locale.localizable.Localizable`.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable,
        description: ResolvableLocalizable | None = None,
    ):
        super().__init__(
            LocalizableDefinition(),
            label=label,
            description=description,
            resolver=resolve_localizable,
        )

    @override
    async def linked_data_schema_for(self, project: Project, /) -> Schema:
        return STATIC_TRANSLATIONS_SCHEMA

    @override
    async def dump_linked_data_for(
        self, project: Project, target: Localizable, /
    ) -> PortableMapping:
        # @todo Refactor dump_context()
        # dump_context(portable, description="https://schema.org/description")
        localizers = await project.public_localizers
        return {
            to_language_tag(locale): translation
            for locale, translation in StaticTranslations.resolve(
                target, localizers
            ).translations.items()
        }
