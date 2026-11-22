"""
The presences content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories import raspberry_mint
from betty.attrs.owner import OwnerAttr
from betty.collections.sequence.list import List
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.datas.aggregate.collection.list import ListDefinition
from betty.datas.aggregate.record.object import Object, ObjectDefinition
from betty.datas.optional import OptionalDefinition
from betty.definition.id import resolve_id
from betty.entities.event import Event
from betty.factory import DataManufacturable, Manufacturable
from betty.freezers.attr import AttrFreezable
from betty.localizables.gettext import _
from betty.machine_name import MachineName
from betty.project import Project
from betty.role import RoleDefinition
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.definition.id import ResolvableId
    from betty.document import Document
    from betty.jinja import Environment


@final
@ObjectDefinition(
    label=_("Presences configuration"),
    samples=(
        Sample(lambda: PresencesConfig(), label="Minimal"),
        Sample(
            lambda: PresencesConfig(include=["subject"]),
            label="Includes",
            size=Size.FULL,
        ),
        Sample(
            lambda: PresencesConfig(exclude=["subject"]),
            label="Excludes",
            size=Size.FULL,
        ),
    ),
)
class PresencesConfig(Object, AttrFreezable):
    """
    Configuration for :py:class:`betty.content_builders.raspberry_mint_presences.Presences`.

    .. data:: betty.content_builders.raspberry_mint_presences:PresencesConfig
    """

    exclude = OwnerAttr(
        ListDefinition(
            value=OptionalDefinition(MachineName.definition), label=_("Exclude")
        )
    ).optional
    """
    The presence roles for which to exclude presences.
    """

    include = OwnerAttr(
        ListDefinition(
            value=OptionalDefinition(MachineName.definition), label=_("Include")
        )
    ).optional
    """
    The presence roles for which to include presences.
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvableId[RoleDefinition] | None] | None = None,
        exclude: Iterable[ResolvableId[RoleDefinition] | None] | None = None,
    ):
        super().__init__()
        if include is not None:
            self.include = List(
                None if include_ is None else resolve_id(include_)
                for include_ in include
            )
        if exclude is not None:
            self.exclude = List(
                None if exclude_ is None else resolve_id(exclude_)
                for exclude_ in exclude
            )


@final
@ContentBuilderDefinition(
    "raspberry-mint-presences",
    label=_("Presences"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Presences(Template, DataManufacturable[PresencesConfig], Manufacturable):
    """
    People's presences at an event.

    .. plugin:: content-builder:raspberry-mint-presences
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvableId[RoleDefinition] | None] | None = None,
        jinja: Environment,
    ):
        super().__init__(jinja=jinja)
        self._include = (
            None
            if include is None
            else tuple(
                None if include_ is None else resolve_id(include_)
                for include_ in include
            )
        )

    @override
    @classmethod
    def new_data_cls(cls) -> type[PresencesConfig]:
        return PresencesConfig

    @override
    @Project.require
    @classmethod
    async def new(
        cls, project: Project, data: PresencesConfig | None = None, /
    ) -> Self:
        if data is None:
            raise NotImplementedError
        include: Iterable[ResolvableId[RoleDefinition]] | None
        if data.include is not None:
            include = data.include
        else:
            roles = project.plugins[RoleDefinition]
            include = {role.id async for role in roles}
            if data.exclude is not None:
                include -= set(data.exclude)
        return cls(include=include, jinja=await project.jinja)

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        if isinstance(document.resource, Event):
            presences = document.resource.presences
            if self._include is not None:
                presences = tuple(
                    presence
                    for presence in presences
                    if (presence.role.definition.id if presence.role else None)
                    in self._include
                )
            if not presences:
                return None
            return "component/raspberry-mint/presences.html.j2", {
                "presences": presences
            }
        return None
