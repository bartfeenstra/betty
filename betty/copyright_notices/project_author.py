"""
The project author copyright notice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.factory import Manufacturable
from betty.freezers.classtools import FrozenOnInit
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from betty.localizer import AnyLocalizable


@final
@CopyrightNoticeDefinition("project-author", label=_("Project author"))
class ProjectAuthor(Manufacturable, CopyrightNotice, FrozenOnInit):
    """
    .. plugin:: copyright-notice:project-author.
    """

    def __init__(self, author: AnyLocalizable | None, /):
        super().__init__()
        self._author = author

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project.author)

    @property
    @override
    def summary(self) -> AnyLocalizable:
        if self._author:
            return _("© Copyright {author}, unless otherwise credited").format(
                author=self._author
            )
        return _("© Copyright the author, unless otherwise credited")

    @property
    @override
    def text(self) -> AnyLocalizable:
        return self.summary
