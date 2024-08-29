"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import final, TYPE_CHECKING

from typing_extensions import override

from betty.plugin.entry_point import EntryPointPluginRepository

if TYPE_CHECKING:
    from betty.plugin import PluginRepository, Plugin
    from betty.locale.localizer import Localizer
    from betty.job import Context
    from pathlib import Path
    from collections.abc import Sequence


class Renderer(ABC):
    """
    Define a (file) content renderer.

    Renderers can be implemented for a variety of purposes:
    - invoking templating engines
    - file conversions

    Read more about :doc:`/development/plugin/renderer`.
    """

    @property
    @abstractmethod
    def file_extensions(self) -> set[str]:
        """
        The extensions of the files this renderer can render.
        """
        pass

    @abstractmethod
    async def render_file(
        self,
        file_path: Path,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> Path:
        """
        Render a single file.

        :return: The file's new path, which may have been changed, e.g. a
            renderer-specific extension may have been stripped from the end.
        """
        pass


RENDERER_REPOSITORY: PluginRepository[Renderer & Plugin] = EntryPointPluginRepository(
    "betty.renderer"
)
"""
The renderer plugin repository.

Read more about :doc:`/development/plugin/renderer`.
"""


@final
class SequentialRenderer(Renderer):
    """
    Render using a sequence of other renderers.
    """

    def __init__(self, renderers: Sequence[Renderer]):
        self._renderers = renderers
        self._file_extensions = {
            file_extension
            for renderer in self._renderers
            for file_extension in renderer.file_extensions
        }

    @override
    @property
    def file_extensions(self) -> set[str]:
        return self._file_extensions

    @override
    async def render_file(
        self,
        file_path: Path,
        *,
        job_context: Context | None = None,
        localizer: Localizer | None = None,
    ) -> Path:
        for renderer in self._renderers:
            if file_path.suffix in renderer.file_extensions:
                return await self.render_file(
                    await renderer.render_file(
                        file_path,
                        job_context=job_context,
                        localizer=localizer,
                    )
                )
        return file_path
