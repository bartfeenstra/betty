from pathlib import Path
from typing import Optional, Iterable, Dict
from urllib.parse import urlparse

from PyQt5.QtWidgets import QFormLayout, QButtonGroup, QRadioButton, QWidget, QHBoxLayout, QLineEdit, \
    QFileDialog, QPushButton
from reactives import reactive
from voluptuous import Schema, Invalid, All, Any

from betty.app import App
from betty.config import ConfigurationError
from betty.generate import Generator
from betty.extension import ConfigurableExtension, Configuration
from betty.extension.nginx.artifact import generate_configuration_file, generate_dockerfile_file
from betty.gui import GuiBuilder, catch_exceptions
from betty.os import PathLike
from betty.serve import ServerProvider, Server


class NginxConfiguration(Configuration):
    def __init__(self, www_directory_path: Optional[PathLike] = None, https: Optional[bool] = None):
        super().__init__()
        self._https = https
        self._www_directory_path = None if www_directory_path is None else Path(www_directory_path)

    @reactive
    @property
    def https(self) -> Optional[bool]:
        return self._https

    @https.setter
    def https(self, https: Optional[bool]) -> None:
        self._https = https

    @reactive
    @property
    def www_directory_path(self) -> Optional[Path]:
        return self._www_directory_path

    @www_directory_path.setter
    def www_directory_path(self, www_directory_path: Optional[Path]) -> None:
        self._www_directory_path = www_directory_path


_NginxConfigurationSchema = Schema(All({
    'www_directory_path': Any(str, None),
    'https': Any(bool, None),
}, lambda configuration_dict: NginxConfiguration(**configuration_dict)))


class Nginx(ConfigurableExtension, Generator, ServerProvider, GuiBuilder):
    @classmethod
    def default_configuration(cls) -> NginxConfiguration:
        return NginxConfiguration()

    @classmethod
    def configuration_from_dict(cls, configuration_dict: Dict) -> NginxConfiguration:
        try:
            return _NginxConfigurationSchema(configuration_dict)
        except Invalid as e:
            raise ConfigurationError(e)

    @classmethod
    def configuration_to_dict(cls, configuration: NginxConfiguration) -> Dict:
        return {
            'www_directory_path': configuration.www_directory_path,
            'https': configuration.https,
        }

    @property
    def servers(self) -> Iterable[Server]:
        from betty.extension.nginx.serve import DockerizedNginxServer

        if DockerizedNginxServer.is_available():
            return [DockerizedNginxServer(self._app)]
        return []

    async def generate(self) -> None:
        await self.generate_configuration_file()
        await self._generate_dockerfile_file()

    @property
    def assets_directory_path(self) -> Optional[Path]:
        return Path(__file__).parent / 'assets'

    @property
    def https(self) -> bool:
        if self._configuration.https is None:
            return self._app.configuration.base_url.startswith('https')
        return self._configuration.https

    @property
    def www_directory_path(self) -> Path:
        if self._configuration.www_directory_path is None:
            return self._app.configuration.www_directory_path
        return self._configuration.www_directory_path

    async def generate_configuration_file(self, destination_file_path: Optional[str] = None, **kwargs) -> None:
        kwargs = dict({
            'server_name': urlparse(self._app.configuration.base_url).netloc,
        }, **kwargs)
        if destination_file_path is None:
            destination_file_path = self._app.configuration.output_directory_path / 'nginx' / 'nginx.conf'
        await generate_configuration_file(destination_file_path, self._app.jinja2_environment, **kwargs)

    async def _generate_dockerfile_file(self) -> None:
        await generate_dockerfile_file(self._app.configuration.output_directory_path / 'nginx' / 'docker' / 'Dockerfile')

    @classmethod
    def gui_name(cls) -> str:
        return 'Nginx'

    @classmethod
    def gui_description(cls) -> str:
        return _('Generate <a href="">nginx</a> configuration for your site, as well as a <code>Dockerfile</code> to build a <a href="https://www.docker.com/">Docker</a> container around it.')

    def gui_build(self) -> Optional[QWidget]:
        return _NginxGuiWidget(self._app, self._configuration)


class _NginxGuiWidget(QWidget):
    def __init__(self, app: App, configuration: NginxConfiguration, *args, **kwargs):
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
            self._configuration.www_directory_path = None if www_directory_path == '' or www_directory_path == self._app.configuration.www_directory_path else www_directory_path
        self._nginx_www_directory_path = QLineEdit()
        self._nginx_www_directory_path.setText(str(self._configuration.www_directory_path) if self._configuration.www_directory_path is not None else str(self._app.configuration.www_directory_path))
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
