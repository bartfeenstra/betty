"""
Create new projects.
"""

from __future__ import annotations

from asyncio import gather, to_thread
from typing import TYPE_CHECKING

from betty.file import write
from betty.localizables.gettext import _
from betty.pathlib import resolve_path
from betty.project import ProjectConfig
from betty.serialize import serializer_for
from betty.user import Severity

if TYPE_CHECKING:
    from betty.app import App
    from betty.pathlib import StrPath


async def new(app: App, config: ProjectConfig, file: StrPath, /) -> None:
    """
    Create a new project.
    """
    file = resolve_path(file)
    await to_thread(file.parent.mkdir, exist_ok=True, parents=True)
    await write(
        file,
        serializer_for(await gather(*app.serializers), file.name).dump(
            ProjectConfig.definition.porter.dump(config)
        ),
    )
    await app.ui.message(
        _("Saved your project to {file}.").format(file=str(file)), Severity.CONFIRM
    )
