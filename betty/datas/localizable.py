"""
Localizable data.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from betty.classtools import Singleton
from betty.data import DataDefinition
from betty.importlib import fully_qualified_name
from betty.linked_data import LinkedData
from betty.linked_data_porters.callback import CallbackLinkedDataPorter
from betty.locale import to_language_tag
from betty.localizable import CountableLocalizable, Localizable, ResolvableLocalizable
from betty.localizables.gettext import _
from betty.localizables.plain import Plain
from betty.localizables.static import CountableStaticTranslations, StaticTranslations
from betty.localizer import default_localizer
from betty.portable.error import NotPortable
from betty.porters.callback import CallbackPorter

if TYPE_CHECKING:
    from betty.portable import PortableData, PortableMapping
    from betty.project import Project


@final
class LocalizableDefinition(DataDefinition[Localizable]):
    """
    The data definition for :py:class:`betty.localizable.Localizable`.
    """

    def __init__(
        self,
        *,
        label: ResolvableLocalizable | None = None,
        description: ResolvableLocalizable | None = None,
        linked_data_context: str | None = None,
    ):
        super().__init__(
            cls=Localizable,
            label=label or _("A localizable string"),
            description=description,
            porter=CallbackPorter(StaticTranslations.load, self._dump),
            linked_data_porter=CallbackLinkedDataPorter(
                self._linked_data_schema, self._dump_linked_data
            ),
        )
        self._linked_data_context = linked_data_context

    def _dump(self, data: Localizable) -> PortableData:
        if isinstance(data, Plain):
            data = StaticTranslations({data.locale: data.text})
        if isinstance(data, StaticTranslations):
            return data.dump()
        raise NotPortable(
            Plain(
                "Only static translations and plain text can be dumped to portable data, not `{localizable}` objects."
            ).format(localizable=fully_qualified_name(type(data)))
        )

    async def _linked_data_schema(self, project: Project, /) -> PortableMapping:
        return {
            "additionalProperties": {
                "type": "string",
                "description": "A human-readable translation.",
            },
            "title": self.label.localize(default_localizer),
            "description": (
                self.description.localize(default_localizer) + " "
                if self.description
                else ""
            )
            + "Keys are IETF BCP-47 language tags.",
        }

    async def _dump_linked_data(
        self, project: Project, data: Localizable, /
    ) -> LinkedData:
        return LinkedData(
            {
                to_language_tag(locale): translation
                for locale, translation in StaticTranslations.resolve(
                    data, await project.public_localizers
                ).translations.items()
            },
            context=self._linked_data_context,
        )


@final
class CountableLocalizableDefinition(DataDefinition[CountableLocalizable], Singleton):
    """
    The data definition for :py:class:`betty.localizable.CountableLocalizable`.
    """

    def __init__(self):
        super().__init__(
            cls=CountableLocalizable,
            label=_("A countable localizable string"),
            porter=CallbackPorter(CountableStaticTranslations.load, self._dump),
        )

    def _dump(self, data: CountableLocalizable) -> PortableData:
        if isinstance(data, CountableStaticTranslations):
            return data.dump()
        raise NotPortable(
            Plain(
                "Only static translations and plain text can be dumped to portable data, not `{localizable}` objects."
            ).format(localizable=fully_qualified_name(type(data)))
        )
