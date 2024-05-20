"""
Provide the Render API.
"""

from pathlib import Path

from typing_extensions import override

from betty.locale import Localizer
from betty.job import Context


class Renderer:
    """
    Define a (file) content renderer.

    Renderers can be implemented for a variety of purposes:
    - invoking templating engines
    - file conversions
    """

    @property
    def file_extensions(self) -> set[str]:
        """
        The extensions of the files this renderer can render.
        """
        raise NotImplementedError(repr(self))

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
        raise NotImplementedError(repr(self))


class SequentialRenderer(Renderer):
    """
    Render using a sequence of other renderers.
    """

    def __init__(self, renderers: list[Renderer]):
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
