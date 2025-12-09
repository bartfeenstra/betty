"""
Provide :py:class:`betty.copyright_notice.CopyrightNotice` plugins.
"""

from typing import Self, final

from typing_extensions import override

from betty.copyright_notice import CopyrightNotice, CopyrightNoticeDefinition
from betty.locale.localizable import Localizable, LocalizableLike
from betty.locale.localizable.ensure import ensure_localizable
from betty.locale.localizable.gettext import _
from betty.project import Project
from betty.project.factory import ProjectDependentSelfFactory


@final
@CopyrightNoticeDefinition("project-author", label=_("Project author"))
class ProjectAuthor(ProjectDependentSelfFactory, CopyrightNotice):
    """
    Copyright belonging to a project author.
    """

    def __init__(self, author: LocalizableLike | None):
        super().__init__()
        self._author = None if author is None else ensure_localizable(author)

    @override
    @classmethod
    async def new_for_project(cls, project: Project, /) -> Self:
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


@final
@CopyrightNoticeDefinition("public-domain", label=_("Public domain"))
class PublicDomain(CopyrightNotice):
    """
    A work is in the `public domain <https://en.wikipedia.org/wiki/Public_domain>`.
    """

    @property
    @override
    def summary(self) -> Localizable:
        return _("Public domain")

    @property
    @override
    def text(self) -> Localizable:
        return _(
            "Works in the public domain can be used or referenced without permission, because nobody holds any exclusive rights over these works (anymore)."
        )
