"""
Provide the Render API.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, final

from typing_extensions import override

from betty.typing import internal

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from betty.job import Context
    from betty.locale.localizer import Localizer


class Renderer(ABC):
    """
    Render content to HTML.

    Read more about :doc:`/development/plugin/renderer`.
    """

    @property
    @abstractmethod
    def file_extensions(self) -> set[str]:
        """
        The extensions of the files this renderer can render.
        """

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


@internal
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
            for renderer_file_extension in renderer.file_extensions:
                if file_path.suffix.endswith(renderer_file_extension):
                    return await renderer.render_file(
                        file_path,
                        job_context=job_context,
                        localizer=localizer,
                    )
        return file_path
