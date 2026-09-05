"""
The project author copyright notice.
"""

from __future__ import annotations

from typing import Self, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.factory import Arg1Manufacturable
from betty.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)
from betty.localizables.gettext import _
from betty.project import Project


@final
@CopyrightNoticeDefinition("project-author", label=_("Project author"))
class ProjectAuthor(Arg1Manufacturable, CopyrightNotice):
    """
    .. plugin:: copyright-notice:project-author.
    """

    def __init__(self, author: ResolvableLocalizable | None):
        super().__init__()
        self._author = None if author is None else resolve_localizable(author)

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(project.author)

    @property
    @override
    def summary(self) -> Localizable:
        if self._author:
            return _("© Copyright {author}, unless otherwise credited").format(
                author=self._author
            )
        return _("© Copyright the author, unless otherwise credited")

    @property
    @override
    def text(self) -> Localizable:
        return self.summary
