"""
Data types to represent names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.ancestry.date import HasDate
from betty.locale.localizable import StaticTranslations

if TYPE_CHECKING:
    from betty.date import DateLike
    from betty.json.linked_data import JsonLdObject
    from betty.locale.localizable import Localizable
    from betty.project import Project
    from betty.serde.dump import Dump, DumpMapping


@final
class Name(HasDate):
    """
    A name.

    A name can be translated, and have a date expressing the period the name was in use.
    """

    def __init__(
        self,
        name: Localizable,
        *,
        date: DateLike | None = None,
    ):
        super().__init__(date=date)
        self.name = name

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property(
            "name", await StaticTranslations.linked_data_schema(project)
        )
        return schema

    @override
    async def dump_linked_data(self, project: Project) -> DumpMapping[Dump]:
        dump = await super().dump_linked_data(project)
        dump["name"] = await StaticTranslations.dump_linked_data_for(project, self.name)
        return dump
