from __future__ import annotations

from betty.extension import Wikipedia
from typing import TYPE_CHECKING

from betty.project import Project

if TYPE_CHECKING:
    from betty.app import App
    from betty.tests.conftest import BettyQtBot


class TestWikipediaGuiWidget:
    async def test_https_with_base_url(
        self, betty_qtbot: BettyQtBot, new_temporary_app: App
    ) -> None:
        async with Project.new_temporary(new_temporary_app) as project:
            project.configuration.extensions.enable(Wikipedia)
            async with project:
                wikipedia = project.extensions[Wikipedia]
                sut = wikipedia.gui_build()
                betty_qtbot.qtbot.addWidget(sut)
                sut.show()

                betty_qtbot.set_checked(sut._populate_images, False)
                assert not wikipedia.configuration.populate_images
