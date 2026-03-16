"""
The project author copyright notice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.locale.localizable import (
    Localizable,
    ResolvableLocalizable,
    resolve_localizable,
)
from betty.locale.localizable.gettext import _
from betty.service.factory import Manufacturable
from betty.service.requirement.project import require_project

if TYPE_CHECKING:
    from betty.project import Project


@final
@CopyrightNoticeDefinition("project-author", label=_("Project author"))
class ProjectAuthor(Manufacturable, CopyrightNotice):
    """
    .. plugin:: copyright-notice:project-author.
    """

    def __init__(self, author: ResolvableLocalizable | None):
        super().__init__()
        self._author = None if author is None else resolve_localizable(author)

    @override
    @classmethod
    @require_project
    async def new(cls, project: Project, /) -> Self:
        return cls(project.configuration.author)

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
