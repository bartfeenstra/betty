"""
The timeline content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.content import ContentDefinition
from betty.factory import Manufacturable
from betty.locale.localizable.gettext import _
from betty.plugins.asset.raspberry_mint import RASPBERRY_MINT
from betty.plugins.content.template import Template, TemplateBuild
from betty.plugins.entity.person import Person
from betty.plugins.entity.place import Place
from betty.plugins.extension._theme import person_timeline_events, place_timeline_events
from betty.project import Project

if TYPE_CHECKING:
    from betty.document import Document
    from betty.jinja import Environment


@final
@ContentDefinition(
    "raspberry-mint-timeline",
    label=_("Timeline"),
    requires={Project.assets.require(RASPBERRY_MINT)},
)
class Timeline(Template, Manufacturable):
    """
    A timeline of events.

    .. plugin:: content:raspberry-mint-timeline
    """

    def __init__(self, *, jinja: Environment, lifetime_threshold: int):
        super().__init__(jinja=jinja)
        self._lifetime_threshold = lifetime_threshold

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(
            jinja=await project.jinja, lifetime_threshold=project.lifetime_threshold
        )

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        events = []
        if isinstance(document.resource, Person):
            events.extend(
                person_timeline_events(document.resource, self._lifetime_threshold)
            )
        elif isinstance(document.resource, Place):
            events.extend(place_timeline_events(document.resource))
        if events:
            return "component/raspberry-mint/timeline.html.j2", {"events": events}
        return None
