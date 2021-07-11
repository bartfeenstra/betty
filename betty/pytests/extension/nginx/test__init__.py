from PyQt5 import QtCore
from PyQt5.QtWidgets import QFileDialog

from betty.app import App
from betty.asyncio import sync
from betty.config import Configuration, ExtensionConfiguration
from betty.extension.nginx import Nginx


@sync
async def test_configuration_https_base_url(tmpdir, qtbot) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    configuration.extensions.add(ExtensionConfiguration(Nginx))
    async with App(configuration) as app:
        sut = app.extensions[Nginx]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        widget._nginx_https_base_url.setChecked(True)

        assert sut._configuration.https is None


@sync
async def test_configuration_https_https(tmpdir, qtbot) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    configuration.extensions.add(ExtensionConfiguration(Nginx))
    async with App(configuration) as app:
        sut = app.extensions[Nginx]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        widget._nginx_https_https.setChecked(True)

        assert sut._configuration.https is True


@sync
async def test_configuration_https_http(tmpdir, qtbot) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    configuration.extensions.add(ExtensionConfiguration(Nginx))
    async with App(configuration) as app:
        sut = app.extensions[Nginx]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        widget._nginx_https_http.setChecked(True)

        assert sut._configuration.https is False


@sync
async def test_configuration_www_directory_path(tmpdir, qtbot) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    configuration.extensions.add(ExtensionConfiguration(Nginx))
    async with App(configuration) as app:
        sut = app.extensions[Nginx]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        www_directory_path = str(tmpdir.join('www-directory-path'))
        widget._nginx_www_directory_path.setText(www_directory_path)

        assert sut._configuration.www_directory_path == www_directory_path


@sync
async def test_configuration_www_directory_path_find(mocker, tmpdir, qtbot) -> None:
    configuration = Configuration(tmpdir, 'https://example.com')
    configuration.extensions.add(ExtensionConfiguration(Nginx))
    async with App(configuration) as app:
        sut = app.extensions[Nginx]
        widget = sut.gui_build()
        qtbot.addWidget(widget)
        widget.show()

        www_directory_path = str(tmpdir.join('www-directory-path'))
        mocker.patch.object(
            QFileDialog,
            'getExistingDirectory',
            mocker.MagicMock(return_value=www_directory_path),
        )
        qtbot.mouseClick(widget._nginx_www_directory_path_find, QtCore.Qt.LeftButton)
        assert sut._configuration.www_directory_path == www_directory_path
