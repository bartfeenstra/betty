from unittest import mock

from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog

from betty.app import App
from betty.asyncio import sync
from betty.config import Configuration, ExtensionConfiguration
from betty.extension.nginx import Nginx
from betty.pytests import QTest


class TestGui(QTest):
    @sync
    async def test_configuration_https_base_url(self, tmpdir, qtbot) -> None:
        configuration = Configuration(tmpdir, 'https://example.com')
        configuration.extensions[Nginx] = ExtensionConfiguration(Nginx)
        async with App(configuration) as app:
            sut = app.extensions[Nginx]
            widget = sut.gui_build()
            qtbot.addWidget(widget)
            widget.show()

            widget._nginx_https_base_url.setChecked(True)

            assert sut._configuration.https is None

    @sync
    async def test_configuration_https_https(self, tmpdir, qtbot) -> None:
        configuration = Configuration(tmpdir, 'https://example.com')
        configuration.extensions[Nginx] = ExtensionConfiguration(Nginx)
        async with App(configuration) as app:
            sut = app.extensions[Nginx]
            widget = sut.gui_build()
            qtbot.addWidget(widget)
            widget.show()

            widget._nginx_https_https.setChecked(True)

            assert sut._configuration.https is True

    @sync
    async def test_configuration_https_http(self, tmpdir, qtbot) -> None:
        configuration = Configuration(tmpdir, 'https://example.com')
        configuration.extensions[Nginx] = ExtensionConfiguration(Nginx)
        async with App(configuration) as app:
            sut = app.extensions[Nginx]
            widget = sut.gui_build()
            qtbot.addWidget(widget)
            widget.show()

            widget._nginx_https_http.setChecked(True)

            assert sut._configuration.https is False

    @sync
    async def test_configuration_www_directory_path(self, tmpdir, qtbot) -> None:
        configuration = Configuration(tmpdir, 'https://example.com')
        configuration.extensions[Nginx] = ExtensionConfiguration(Nginx)
        async with App(configuration) as app:
            sut = app.extensions[Nginx]
            widget = sut.gui_build()
            qtbot.addWidget(widget)
            widget.show()

            www_directory_path = str(tmpdir.join('www-directory-path'))
            widget._nginx_www_directory_path.setText(www_directory_path)

            assert sut._configuration.www_directory_path == www_directory_path

    @sync
    async def test_configuration_www_directory_path_find(self, mocker, tmpdir, qtbot) -> None:
        configuration = Configuration(tmpdir, 'https://example.com')
        configuration.extensions[Nginx] = ExtensionConfiguration(Nginx)
        async with App(configuration) as app:
            sut = app.extensions[Nginx]
            widget = sut.gui_build()
            qtbot.addWidget(widget)
            widget.show()

            www_directory_path = str(tmpdir.join('www-directory-path'))
            mocker.patch.object(
                QFileDialog,
                'getExistingDirectory',
                mock.MagicMock(return_value=www_directory_path),
            )
            qtbot.mouseClick(widget._nginx_www_directory_path_find, QtCore.Qt.LeftButton)
            assert sut._configuration.www_directory_path == www_directory_path
