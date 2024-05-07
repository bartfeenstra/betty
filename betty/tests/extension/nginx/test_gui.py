from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QFileDialog
from pytest_mock import MockerFixture

from betty.extension import Nginx
from betty.tests.conftest import BettyQtBot


class TestNginxGuiWidget:
    async def test_https_with_base_url(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(Nginx)
        nginx = betty_qtbot.app.extensions[Nginx]
        nginx.configuration.https = False
        sut = nginx.gui_build()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.set_checked(sut._nginx_https_base_url, True)
        assert nginx.configuration.https is None

    async def test_https_with_https(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(Nginx)
        nginx = betty_qtbot.app.extensions[Nginx]
        nginx.configuration.https = False
        sut = nginx.gui_build()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.set_checked(sut._nginx_https_https, True)
        assert nginx.configuration.https is True

    async def test_https_with_http(
        self,
        betty_qtbot: BettyQtBot,
    ) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(Nginx)
        nginx = betty_qtbot.app.extensions[Nginx]
        nginx.configuration.https = True
        sut = nginx.gui_build()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.set_checked(sut._nginx_https_http, True)
        assert nginx.configuration.https is False

    async def test_www_directory_path_with_path(
        self,
        betty_qtbot: BettyQtBot,
        mocker: MockerFixture,
        tmp_path: Path,
    ) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(Nginx)
        nginx = betty_qtbot.app.extensions[Nginx]
        sut = nginx.gui_build()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        www_directory_path = str(tmp_path)
        mocker.patch.object(
            QFileDialog,
            "getExistingDirectory",
            mocker.MagicMock(return_value=www_directory_path),
        )

        betty_qtbot.mouse_click(sut._nginx_www_directory_path_find)
        assert nginx.configuration.www_directory_path == www_directory_path

    async def test_www_directory_path_without_path(
        self,
        betty_qtbot: BettyQtBot,
        tmp_path: Path,
    ) -> None:
        betty_qtbot.app.project.configuration.extensions.enable(Nginx)
        nginx = betty_qtbot.app.extensions[Nginx]
        sut = nginx.gui_build()
        betty_qtbot.qtbot.addWidget(sut)
        sut.show()

        betty_qtbot.set_text(sut._nginx_www_directory_path, "")
        assert nginx.configuration.www_directory_path is None
