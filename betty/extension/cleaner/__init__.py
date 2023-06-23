from __future__ import annotations

from betty.app.extension import UserFacingExtension, Extension
from betty.cleaner import clean
from betty.load import PostLoader
from betty.locale import Localizer


class _Cleaner(UserFacingExtension, PostLoader):
    @classmethod
    def comes_after(cls) -> set[type[Extension]]:
        from betty.extension import Anonymizer

        return {Anonymizer}

    async def post_load(self) -> None:
        clean(self.app.project.ancestry)

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Cleaner')

    @classmethod
    def description(cls, localizer: Localizer) -> str:
        return localizer._('Remove people, events, places, files, sources, and citations if they have no relationships with any other resources. Enable the Privatizer and Anonymizer as well to make this most effective.')
