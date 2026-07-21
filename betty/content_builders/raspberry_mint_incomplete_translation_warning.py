"""
The incomplete translation warning content plugin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self, final, override

from polib import pofile

from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.concurrent import Ledger, ThreadSafeLock
from betty.content_builder import ContentBuilderDefinition
from betty.content_builders.template import Template, TemplateBuild
from betty.dirs import builtin_asset_directory
from betty.factory import Manufacturable
from betty.file import read
from betty.locale import default_locale, to_language_tag
from betty.project import Project

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping
    from pathlib import Path

    from babel import Locale
    from jinja2 import Environment

    from betty.document import Document


@final
@ContentBuilderDefinition(
    "raspberry-mint-incomplete-translation-warning",
    label="Incomplete translation warning",
    requires={Project.asset_directories.require(raspberry_mint)},
)
class IncompleteTranslationWarning(Template, Manufacturable):
    """
    .. plugin:: content-builder:raspberry-mint-incomplete-translation-warning.
    """

    def __init__(self, *, asset_directories: Iterable[Path], jinja: Environment):
        super().__init__(jinja=jinja)
        self._asset_directories = tuple(asset_directories)
        self._ledger = Ledger(ThreadSafeLock())
        self._completions: MutableMapping[Locale, int] = {
            default_locale: 100,
        }

    @override
    @Project.require
    @classmethod
    async def new(cls, project: Project, /) -> Self:
        return cls(
            asset_directories=project.asset_directories.directories,
            jinja=await project.jinja,
        )

    async def _completion(self, locale: Locale, /) -> int:
        completion = self._completions.get(locale, None)
        if completion is not None:
            return completion
        async with self._ledger.ledger(str(locale)):
            completion = self._completions.get(locale, None)
            if completion is not None:
                return completion
            try:
                po = await read(
                    builtin_asset_directory
                    / "locale"
                    / to_language_tag(locale)
                    / "betty.po"
                )
            except FileNotFoundError:
                self._completions[locale] = 0
            else:
                entries = [entry.translated() for entry in pofile(po)]
                self._completions[locale] = round(
                    100 * entries.count(True) / len(entries)
                )
            return self._completions[locale]

    @override
    async def build_template(self, document: Document) -> TemplateBuild:
        completion = await self._completion(document.localizer.locale)
        if completion == 100:
            return None
        return "component/raspberry-mint/incomplete-translation-warning.html.j2", {
            "incomplete_translation_warning_percentage": completion,
        }
