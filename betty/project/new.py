"""
Create new projects.
"""

from __future__ import annotations

from asyncio import gather
from typing import TYPE_CHECKING

from betty.locale.localizable.gettext import _
from betty.portable.file import dump_file

if TYPE_CHECKING:
    from betty.app import App
    from betty.pathlib import StrPath
    from betty.project.data import ProjectConfiguration


async def new(
    app: App, configuration: ProjectConfiguration, configuration_file: StrPath, /
) -> None:
    """
    Create a new project.
    """
    await dump_file(
        configuration.data().porter.dump(configuration),
        configuration_file,
        serializers=await gather(*app.serializers),
    )
    await app.user.message_information(
        _("Saved your project to {configuration_file}.").format(
            configuration_file=str(configuration_file)
        )
    )
