"""
Describe localized information.
"""

from __future__ import annotations

from contextlib import suppress
from typing import Any, Sequence, TYPE_CHECKING

from typing_extensions import override

from betty.json.linked_data import LinkedDataDumpable
from betty.json.schema import ref_locale
from betty.locale import Localey, negotiate_locale, to_locale
from betty.serde.dump import DumpMapping, Dump, dump_default

if TYPE_CHECKING:
    from betty.project import Project


class Localized(LinkedDataDumpable):
    """
    A resource that is localized, e.g. contains information in a specific locale.
    """

    locale: str | None

    def __init__(
        self,
        *args: Any,
        locale: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(*args, **kwargs)
        self.locale = locale

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        if self.locale is not None:
            dump["locale"] = self.locale
        return dump

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> DumpMapping[Dump]:
        schema = await super().linked_data_schema(project)
        properties = dump_default(schema, "properties", dict)
        properties["locale"] = ref_locale(schema)
        return schema


def negotiate_localizeds(
    preferred_locales: Localey | Sequence[Localey], localizeds: Sequence[Localized]
) -> Localized | None:
    """
    Negotiate the preferred localized value from a sequence.
    """
    negotiated_locale_data = negotiate_locale(
        preferred_locales,
        [localized.locale for localized in localizeds if localized.locale is not None],
    )
    if negotiated_locale_data is not None:
        negotiated_locale = to_locale(negotiated_locale_data)
        for localized in localizeds:
            if localized.locale == negotiated_locale:
                return localized
    for localized in localizeds:
        if localized.locale is None:
            return localized
    with suppress(IndexError):
        return localizeds[0]
    return None
