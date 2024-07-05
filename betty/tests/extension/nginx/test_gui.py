from __future__ import annotations


from PyQt6.QtWidgets import QFileDialog

from betty.extension import Nginx
from typing import TYPE_CHECKING

from betty.project import Project

if TYPE_CHECKING:
    from betty.app import App
    from betty.tests.conftest import BettyQtBot
    from pytest_mock import MockerFixture
    from pathlib import Path


class TestNginxGuiWidget:
    async def test_https_with_base_url(
        self, betty_qtbot: BettyQtBot, new_temporary_app: App
    ) -> None:
        project = Project(new_temporary_app)
        project.configuration.extensions.enable(Nginx)
        async with project:
            nginx = project.extensions[Nginx]
            nginx.configuration.https = False
            sut = nginx.gui_build()
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            betty_qtbot.set_checked(sut._nginx_https_base_url, True)
            assert nginx.configuration.https is None

    async def test_https_with_https(
        self, betty_qtbot: BettyQtBot, new_temporary_app: App
    ) -> None:
        project = Project(new_temporary_app)
        project.configuration.extensions.enable(Nginx)
        async with project:
            nginx = project.extensions[Nginx]
            nginx.configuration.https = False
            sut = nginx.gui_build()
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            betty_qtbot.set_checked(sut._nginx_https_https, True)
            assert nginx.configuration.https is True

    async def test_https_with_http(
        self, betty_qtbot: BettyQtBot, new_temporary_app: App
    ) -> None:
        project = Project(new_temporary_app)
        project.configuration.extensions.enable(Nginx)
        async with project:
            nginx = project.extensions[Nginx]
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
        new_temporary_app: App,
        tmp_path: Path,
    ) -> None:
        project = Project(new_temporary_app)
        project.configuration.extensions.enable(Nginx)
        async with project:
            nginx = project.extensions[Nginx]
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
        new_temporary_app: App,
        tmp_path: Path,
    ) -> None:
        project = Project(new_temporary_app)
        project.configuration.extensions.enable(Nginx)
        async with project:
            nginx = project.extensions[Nginx]
            sut = nginx.gui_build()
            betty_qtbot.qtbot.addWidget(sut)
            sut.show()

            betty_qtbot.set_text(sut._nginx_www_directory_path, "")
            assert nginx.configuration.www_directory_path is None
