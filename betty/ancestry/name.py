"""
Data types to represent names.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, final, override

from betty.ancestry.date import HasDate
from betty.locale.localizable.gettext import _
from betty.locale.localizable.linked_data import dump_linked_data
from betty.locale.localizable.property import LocalizableProperty
from betty.locale.localizable.static.schema import StaticTranslationsSchema

if TYPE_CHECKING:
    from betty.date import ResolvableDate
    from betty.json.linked_data import JsonLdObject
    from betty.locale.localizable import ResolvableLocalizable
    from betty.portable import PortableMapping
    from betty.project import Project


@final
class Name(HasDate):
    """
    A name.

    A name can be translated, and have a date expressing the period the name was in use.
    """

    name = LocalizableProperty(label=_("Name"))

    def __init__(
        self,
        name: ResolvableLocalizable,
        *,
        date: ResolvableDate | None = None,
    ):
        super().__init__(date=date)
        self.name = name

    @override
    @classmethod
    async def linked_data_schema(cls, project: Project, /) -> JsonLdObject:
        schema = await super().linked_data_schema(project)
        schema.add_property("name", StaticTranslationsSchema())
        return schema

    @override
    async def dump_linked_data(self, project: Project, /) -> PortableMapping:
        linked_data = dict(await super().dump_linked_data(project))
        linked_data["name"] = dump_linked_data(
            self.name, localizers=await project.public_localizers
        )
        return linked_data
