from __future__ import annotations

from betty.anonymizer import anonymize, AnonymousCitation, AnonymousSource
from betty.app.extension import UserFacingExtension, Extension
from betty.load import PostLoader
from betty.locale import Localizer


class _Anonymizer(UserFacingExtension, PostLoader):
    @classmethod
    def comes_after(cls) -> set[type[Extension]]:
        from betty.extension import Privatizer

        return {Privatizer}

    async def post_load(self) -> None:
        anonymize(self.app.project.ancestry, AnonymousCitation(AnonymousSource()))

    @classmethod
    def label(cls, localizer: Localizer) -> str:
        return localizer._('Anonymizer')

    @classmethod
    def description(cls, localizer: Localizer) -> str:
        return localizer._('Anonymize people, events, files, sources, and citations marked private by removing their information and relationships with other resources. Enable the Privatizer and Cleaner as well to make this most effective.')
