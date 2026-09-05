"""
The presences content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.attrs.owner import OwnerAttr
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.data import Data
from betty.data.factory import DataManufacturable
from betty.datas.aggregate.collection.sequence import SequenceDefinition
from betty.datas.aggregate.record.object import ObjectDefinition
from betty.entities.event import Event
from betty.factory import Arg1Manufacturable
from betty.localizables.gettext import _
from betty.machine_name import MachineName
from betty.plugin.resolve import ResolvablePluginId, resolve_plugin_id
from betty.project import Project
from betty.prop import HasProps
from betty.role import RoleDefinition
from betty.sample import Sample, Size

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.document import Document
    from betty.jinja import Environment


@final
@ObjectDefinition(
    label=_("Presences configuration"),
    samples=[
        lambda: Sample(PresencesData(), label="Minimal"),
        lambda: Sample(
            PresencesData(include=["subject"]),
            label="Includes",
            size=Size.FULL,
        ),
        lambda: Sample(
            PresencesData(exclude=["subject"]),
            label="Excludes",
            size=Size.FULL,
        ),
    ],
)
class PresencesData(Data, HasProps):
    """
    Configuration for :py:class:`betty.content_builders.raspberry_mint_presences.Presences`.

    .. data:: betty.content_builders.raspberry_mint_presences:PresencesData
    """

    exclude = OwnerAttr(
        SequenceDefinition(cls=list, value=MachineName, label=_("Exclude"))
    ).optional
    """
    The presence roles for which to exclude presences.
    """

    include = OwnerAttr(
        SequenceDefinition(cls=list, value=MachineName, label=_("Include"))
    ).optional
    """
    The presence roles for which to include presences.
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvablePluginId[RoleDefinition]] | None = None,
        exclude: Iterable[ResolvablePluginId[RoleDefinition]] | None = None,
    ):
        super().__init__()
        if include is not None:
            self.include = list(map(resolve_plugin_id, include))
        if exclude is not None:
            self.exclude = list(map(resolve_plugin_id, exclude))


@final
@ContentBuilderDefinition(
    "raspberry-mint-presences",
    label=_("Presences"),
    requires={Project.asset_directories.require(raspberry_mint)},
)
class Presences(
    Template, DataManufacturable[Project, PresencesData], Arg1Manufacturable[Project]
):
    """
    People's presences at an event.

    .. plugin:: content-builder:raspberry-mint-presences
    """

    def __init__(
        self,
        *,
        include: Iterable[ResolvablePluginId[RoleDefinition]] | None = None,
        jinja: Environment,
    ):
        super().__init__(jinja=jinja)
        self._include = (
            None if include is None else tuple(map(resolve_plugin_id, include))
        )

    @override
    @classmethod
    def new_data_cls(cls) -> type[PresencesData]:
        return PresencesData

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, data: PresencesData | None = None, /) -> Self:

        if data is None:
            raise NotImplementedError
        include: Iterable[ResolvablePluginId[RoleDefinition]] | None
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
                    if presence.role.plugin().id in self._include
                )
            if not presences:
                return None
            return "component/raspberry-mint/presences.html.j2", {
                "presences": presences
            }
        return None
