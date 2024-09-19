"""
Provide :py:class:`betty.copyright.Copyright` plugins.
"""

from typing import Self

from typing_extensions import override

from betty.copyright import Copyright
from betty.locale.localizable import _, Localizable
from betty.plugin import ShorthandPluginBase
from betty.project import Project
from betty.project.factory import ProjectDependentFactory


class ProjectAuthor(ShorthandPluginBase, ProjectDependentFactory, Copyright):
    """
    Copyright belonging to a project author.
    """

    _plugin_id = "project-author"
    _plugin_label = _("Project author")

    def __init__(self, author: Localizable | None):
        self._author = author

    @override
    @classmethod
    async def new(cls, project: Project) -> Self:
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
