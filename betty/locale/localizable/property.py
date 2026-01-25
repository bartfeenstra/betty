"""
Localizable attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, final

from typing_extensions import override

from betty.data.aggregate.record.object.property import Property
from betty.json.linked_data import LinkedDataDumper
from betty.locale import to_language_tag
from betty.locale.localizable import (
    CountableLocalizable,
    CountableLocalizableLike,
    Localizable,
    LocalizableLike,
)
from betty.locale.localizable.data import (
    CountableLocalizableDefinition,
    LocalizableDefinition,
)
from betty.locale.localizable.ensure import (
    ensure_countable_localizable,
    ensure_localizable,
)
from betty.locale.localizable.static import StaticTranslations
from betty.locale.localizable.static.schema import StaticTranslationsSchema
from betty.privacy import is_private
from betty.typing import Void

if TYPE_CHECKING:
    from betty.json.schema import Schema
    from betty.portable import PortableData
    from betty.project import Project

_ValueGetT = TypeVar("_ValueGetT")
_ValueSetT = TypeVar("_ValueSetT")


@final
class LocalizableProperty(
    LinkedDataDumper[Any], Property[Localizable, LocalizableLike]
):
    """
    A property containing a :py:class:`betty.locale.localizable.Localizable`.
    """

    def __init__(
        self,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        super().__init__(
            LocalizableDefinition(),
            label=label,
            description=description,
            resolver=ensure_localizable,
        )

    @override
    async def linked_data_schema(self, project: Project, /) -> Schema:
        return StaticTranslationsSchema()

    @override
    async def dump_linked_data(
        self, project: Project, target: Any, /
    ) -> PortableData | Void:
        if is_private(target):
            return Void()
        return {
            to_language_tag(locale): translation
            for locale, translation in StaticTranslations.from_localizable(
                self.__get__(target, type(target)), await project.public_localizers
            ).translations.items()
        }


@final
class CountableLocalizableProperty(
    Property[CountableLocalizable, CountableLocalizableLike]
):
    """
    A property containing a :py:class:`betty.locale.localizable.CountableLocalizable`.
    """

    def __init__(
        self,
        *,
        label: LocalizableLike,
        description: LocalizableLike | None = None,
    ):
        super().__init__(
            CountableLocalizableDefinition(),
            label=label,
            description=description,
            resolver=ensure_countable_localizable,
        )
