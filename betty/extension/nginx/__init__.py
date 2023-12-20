from collections.abc import Sequence
from pathlib import Path
from typing import Any, Self

from PyQt6.QtWidgets import QFormLayout, QButtonGroup, QRadioButton, QWidget, QHBoxLayout, QLineEdit, \
    QFileDialog, QPushButton
from reactives.instance.property import reactive_property

from betty.app import App
from betty.app.extension import ConfigurableExtension
from betty.config import Configuration
from betty.extension.nginx.artifact import generate_configuration_file, generate_dockerfile_file
from betty.generate import Generator, GenerationContext
from betty.gui import GuiBuilder
from betty.gui.error import catch_exceptions
from betty.locale import Str
from betty.serde.dump import Dump, VoidableDump, minimize, Void, VoidableDictDump
from betty.serde.load import Asserter, Fields, OptionalField, Assertions
from betty.serve import ServerProvider, Server


class NginxConfiguration(Configuration):
    def __init__(self, www_directory_path: str | None = None, https: bool | None = None):
        super().__init__()
        self._https = https
        self.www_directory_path = www_directory_path

    @property
    @reactive_property
    def https(self) -> bool | None:
        return self._https

    @https.setter
    def https(self, https: bool | None) -> None:
        self._https = https

    @property
    @reactive_property
    def www_directory_path(self) -> str | None:
        return self._www_directory_path

    @www_directory_path.setter
    def www_directory_path(self, www_directory_path: str | None) -> None:
        self._www_directory_path = www_directory_path

    def update(self, other: Self) -> None:
        self._https = other._https
        self._www_directory_path = other._www_directory_path

    @classmethod
    def load(
        cls,
        dump: Dump,
        configuration: Self | None = None,
    ) -> Self:
        if configuration is None:
            configuration = cls()
        asserter = Asserter()
        asserter.assert_record(Fields(
            OptionalField(
                'https',
                Assertions(asserter.assert_or(asserter.assert_bool(), asserter.assert_none())) | asserter.assert_setattr(configuration, 'https'),
            ),
            OptionalField(
                'www_directory_path',
                Assertions(asserter.assert_str()) | asserter.assert_setattr(configuration, 'www_directory_path'),
            ),
        ))(dump)
        return configuration

    def dump(self) -> VoidableDump:
        dump: VoidableDictDump[VoidableDump] = {
            'https': self.https,
            'www_directory_path': Void if self.www_directory_path is None else str(self.www_directory_path),
        }
        return minimize(dump, True)


class _Nginx(ConfigurableExtension[NginxConfiguration], Generator, ServerProvider, GuiBuilder):
    @classmethod
    def label(cls) -> Str:
        return Str.plain('Nginx')

    @classmethod
    def description(cls) -> Str:
        return Str._('Generate <a href="">nginx</a> configuration for your site, as well as a <code>Dockerfile</code> to build a <a href="https://www.docker.com/">Docker</a> container around it.')

    @classmethod
    def default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

    @property
    def servers(self) -> Sequence[Server]:
        from betty.extension.nginx.serve import DockerizedNginxServer

        if DockerizedNginxServer.is_available():
            return [DockerizedNginxServer(self._app)]
        return []

    async def generate(self, task_context: GenerationContext) -> None:
        await generate_configuration_file(self._app)
        await generate_dockerfile_file(self._app)

    @classmethod
    def assets_directory_path(cls) -> Path | None:
        return Path(__file__).parent / 'assets'

    @property
    def https(self) -> bool:
        if self._configuration.https is None:
            return self._app.project.configuration.base_url.startswith('https')
        return self._configuration.https

    @property
    def www_directory_path(self) -> str:
        return self._configuration.www_directory_path or str(self._app.project.configuration.www_directory_path)

    def gui_build(self) -> QWidget:
        return _NginxGuiWidget(self._app, self._configuration)


class _NginxGuiWidget(QWidget):
    def __init__(self, app: App, configuration: NginxConfiguration, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._app = app
        self._configuration = configuration
        layout = QFormLayout()

        self.setLayout(layout)

        https_button_group = QButtonGroup()

        def _update_configuration_https_base_url(checked: bool) -> None:
            if checked:
                self._configuration.https = None
        self._nginx_https_base_url = QRadioButton("Use HTTPS and HTTP/2 if the site's URL starts with https://")
        self._nginx_https_base_url.setChecked(self._configuration.https is None)
        self._nginx_https_base_url.toggled.connect(_update_configuration_https_base_url)
        layout.addRow(self._nginx_https_base_url)
        https_button_group.addButton(self._nginx_https_base_url)

        def _update_configuration_https_https(checked: bool) -> None:
            if checked:
                self._configuration.https = True
        self._nginx_https_https = QRadioButton('Use HTTPS and HTTP/2')
        self._nginx_https_https.setChecked(self._configuration.https is True)
        self._nginx_https_https.toggled.connect(_update_configuration_https_https)
        layout.addRow(self._nginx_https_https)
        https_button_group.addButton(self._nginx_https_https)

        def _update_configuration_https_http(checked: bool) -> None:
            if checked:
                self._configuration.https = False
        self._nginx_https_http = QRadioButton('Use HTTP')
        self._nginx_https_http.setChecked(self._configuration.https is False)
        self._nginx_https_http.toggled.connect(_update_configuration_https_http)
        layout.addRow(self._nginx_https_http)
        https_button_group.addButton(self._nginx_https_http)

        def _update_configuration_www_directory_path(www_directory_path: str) -> None:
            self._configuration.www_directory_path = None if www_directory_path == '' or www_directory_path == str(self._app.project.configuration.www_directory_path) else www_directory_path
        self._nginx_www_directory_path = QLineEdit()
        self._nginx_www_directory_path.setText(str(self._configuration.www_directory_path) if self._configuration.www_directory_path is not None else str(self._app.project.configuration.www_directory_path))
        self._nginx_www_directory_path.textChanged.connect(_update_configuration_www_directory_path)
        www_directory_path_layout = QHBoxLayout()
        www_directory_path_layout.addWidget(self._nginx_www_directory_path)

        @catch_exceptions
        def find_www_directory_path() -> None:
            found_www_directory_path = QFileDialog.getExistingDirectory(self, 'Serve your site from...', directory=self._nginx_www_directory_path.text())
            if '' != found_www_directory_path:
                self._nginx_www_directory_path.setText(found_www_directory_path)
        self._nginx_www_directory_path_find = QPushButton('...')
        self._nginx_www_directory_path_find.released.connect(find_www_directory_path)
        www_directory_path_layout.addWidget(self._nginx_www_directory_path_find)
        layout.addRow('WWW directory', www_directory_path_layout)
