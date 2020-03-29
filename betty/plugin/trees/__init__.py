import hashlib
import shutil
from contextlib import suppress
from os import path
from os.path import dirname
from subprocess import check_call
from typing import Optional, List, Tuple, Type, Callable, Dict, Iterable

from betty.event import Event
from betty.fs import DirectoryBackup
from betty.jinja2 import HtmlProvider, create_environment, render_tree
from betty.plugin import Plugin
from betty.render import PostRenderEvent
from betty.site import Site


class Trees(Plugin, HtmlProvider):
    def __init__(self, site: Site):
        self._site = site

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site)

    def subscribes_to(self) -> List[Tuple[Type[Event], Callable]]:
        return [
            (PostRenderEvent, self._render),
        ]

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)

    async def _render(self, event: PostRenderEvent) -> None:
        build_directory_path = path.join(self._site.configuration.cache_directory_path, self.name(), hashlib.md5(self.resource_directory_path.encode()).hexdigest())

        environment = create_environment(self._site)
        plugin_build_directory_path = path.join(
            build_directory_path, self.name())
        with DirectoryBackup(plugin_build_directory_path, 'node_modules'):
            with suppress(FileNotFoundError):
                shutil.rmtree(plugin_build_directory_path)
            shutil.copytree(path.join(self.resource_directory_path, 'js'),
                            plugin_build_directory_path)
        await render_tree(plugin_build_directory_path, environment)

        js_plugin_build_directory_path = path.join(
            build_directory_path, self.name())

        # Install third-party dependencies.
        check_call(['npm', 'install', '--production'],
                   cwd=js_plugin_build_directory_path)

        # Run Webpack.
        self._site.resources.copy2(path.join(self._site.configuration.www_directory_path, 'betty.css'), path.join(
            js_plugin_build_directory_path, 'betty.css'))
        check_call(['npm', 'run', 'webpack'],
                   cwd=js_plugin_build_directory_path)
        shutil.copy2(path.join(build_directory_path, 'output', 'trees.css'), path.join(
            self._site.configuration.www_directory_path, 'trees.css'))
        shutil.copy2(path.join(build_directory_path, 'output', 'trees.js'), path.join(
            self._site.configuration.www_directory_path, 'trees.js'))

    @property
    def css_paths(self) -> Iterable[str]:
        return {
            self._site.static_url_generator.generate('trees.css'),
        }

    @property
    def js_paths(self) -> Iterable[str]:
        return {
            self._site.static_url_generator.generate('trees.js'),
        }
