from __future__ import annotations

from betty.extension import Wikipedia
from betty.tests.conftest import BettyQtBot


class TestWikipediaGuiWidget:
    async def test_https_with_base_url(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(Wikipedia)
        wikipedia = betty_qtbot.app.extensions[Wikipedia]
        sut = wikipedia.gui_build()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.set_checked(sut._populate_images, False)
        assert not wikipedia.configuration.populate_images
