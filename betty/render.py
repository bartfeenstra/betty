"""
Provide the Render API.
"""

from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path
from typing import final

from typing_extensions import override

from betty.job import Context
from betty.locale.localizer import Localizer


class Renderer(ABC):
    """
    Define a (file) content renderer.

    Renderers can be implemented for a variety of purposes:
    - invoking templating engines
    - file conversions
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
