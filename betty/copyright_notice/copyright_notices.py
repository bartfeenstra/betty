"""
Provide :py:class:`betty.copyright_notice.CopyrightNotice` plugins.
"""

from typing import Self

from typing_extensions import override

from betty.copyright_notice import CopyrightNotice
from betty.locale.localizable import _, Localizable
from betty.plugin import ShorthandPluginBase
from betty.project import Project
from betty.project.factory import ProjectDependentFactory


class ProjectAuthor(ShorthandPluginBase, ProjectDependentFactory, CopyrightNotice):
    """
    Copyright belonging to a project author.
    """

    _plugin_id = "project-author"
    _plugin_label = _("Project author")

    def __init__(self, author: Localizable | None):
        self._author = author

    @override
    @classmethod
    async def new_for_project(cls, project: Project) -> Self:
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


class PublicDomain(ShorthandPluginBase, CopyrightNotice):
    """
    A work is in the `public domain <https://en.wikipedia.org/wiki/Public_domain>`.
    """

    _plugin_id = "public-domain"
    _plugin_label = _("Public domain")

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
