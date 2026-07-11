"""
Locale attributes.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from betty.attr import Object
from betty.attrs.owner import OwnerAttr
from betty.attrs.privacy import HasPrivacy
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.datas.locale import LocaleDefinition
from betty.linked_data import LinkedData
from betty.locale import ResolvableLocale, resolve_locale, to_language_tag
from betty.localized import Localized
from betty.typing import Voidable, VoidableType

if TYPE_CHECKING:
    from collections.abc import Mapping

    from babel import Locale

    from betty.attrs.common import CommonAttr
    from betty.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project
    from betty.typing import VoidType


def new_locale_attr(
    *,
    label: ResolvableLocalizable | None = None,
    description: ResolvableLocalizable | None = None,
) -> CommonAttr[Object, Locale, ResolvableLocale]:
    """
    Create an attribute containing a locale.
    """
    return OwnerAttr(LocaleDefinition(label=label, description=description)).setter(
        resolve_locale
    )


class HasLocale[DataDefinitionT: ObjectDefinition = ObjectDefinition](
    Localized, Object[DataDefinitionT]
):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    locale = new_locale_attr().optional

    def __init__(
        self, *args: Any, locale: ResolvableLocale | None = None, **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.locale = locale

    @override
    @classmethod
    async def linked_data_schema_properties(
        cls, project: Project, /
    ) -> Mapping[str, VoidableType[PortableMapping]]:
        return {
            "locale": Voidable({
                "oneOf": [
                    {
                        "$ref": "#/$defs/locale",
                    },
                    {
                        "type": "null",
                    },
                ],
                "$defs": {
                    "locale": {
                        "title": "Locale",
                        "description": "A BCP 47 locale identifier (https://www.ietf.org/rfc/bcp/bcp47.txt).",
                    }
                },
            }),
        }

    @override
    async def dump_linked_data_properties(
        self, project: Project, /
    ) -> Mapping[str, LinkedData | VoidType]:
        if isinstance(self, HasPrivacy) and self.private:
            return {}
        return {
            "locale": LinkedData(
                None if self.locale is None else to_language_tag(self.locale)
            )
        }
