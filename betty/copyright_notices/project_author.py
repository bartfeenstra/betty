"""
The project author copyright notice.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, final, override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.localizables.gettext import _
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable

    from betty.localizable import Localizable
    from betty.plugin.discovery import ResolvableDiscovery


@Project.require
def _discover(
    project: Project,
) -> Iterable[ResolvableDiscovery[CopyrightNoticeDefinition]]:
    @final
    @CopyrightNoticeDefinition("project-author", label=_("Project author"))
    class _ProjectAuthor(CopyrightNotice):
        _author: ClassVar[Localizable | None] = project.author

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

    yield _ProjectAuthor
