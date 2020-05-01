import hashlib
import shutil
from contextlib import suppress
from os import path
from os.path import dirname
from subprocess import check_call
from typing import Optional, List, Tuple, Type, Callable, Iterable, Any

from betty.event import Event
from betty.fs import DirectoryBackup
from betty.jinja2 import HtmlProvider
from betty.plugin import Plugin, NO_CONFIGURATION
from betty.generate import PostGenerateEvent
from betty.site import Site


class Maps(Plugin, HtmlProvider):
    def __init__(self, site: Site):
        self._site = site

    @classmethod
    def for_site(cls, site: Site, configuration: Any = NO_CONFIGURATION):
        return cls(site)

    def subscribes_to(self) -> List[Tuple[Type[Event], Callable]]:
        return [
            (PostGenerateEvent, self._render),
        ]

    @property
    def assets_directory_path(self) -> Optional[str]:
        return '%s/assets' % dirname(__file__)

    async def _render(self, event: PostGenerateEvent) -> None:
        build_directory_path = path.join(self._site.configuration.cache_directory_path, self.name(), hashlib.md5(self.assets_directory_path.encode()).hexdigest())

        plugin_build_directory_path = path.join(
            build_directory_path, self.name())
        async with DirectoryBackup(plugin_build_directory_path, 'node_modules'):
            with suppress(FileNotFoundError):
                shutil.rmtree(plugin_build_directory_path)
            shutil.copytree(path.join(self.assets_directory_path, 'js'),
                            plugin_build_directory_path)
        await self._site.renderer.render_tree(plugin_build_directory_path)

        js_plugin_build_directory_path = path.join(
            build_directory_path, self.name())

        # Install third-party dependencies.
        check_call(['npm', 'install', '--production'],
                   cwd=js_plugin_build_directory_path)

        # Run Webpack.
        await self._site.assets.copy2(path.join(self._site.configuration.www_directory_path, 'betty.css'), path.join(
            js_plugin_build_directory_path, 'betty.css'))
        check_call(['npm', 'run', 'webpack'],
                   cwd=js_plugin_build_directory_path)
        shutil.copytree(path.join(build_directory_path, 'output', 'images'), path.join(
            self._site.configuration.www_directory_path, 'images'))
        shutil.copy2(path.join(build_directory_path, 'output', 'maps.css'), path.join(
            self._site.configuration.www_directory_path, 'maps.css'))
        shutil.copy2(path.join(build_directory_path, 'output', 'maps.js'), path.join(
            self._site.configuration.www_directory_path, 'maps.js'))

    @property
    def css_paths(self) -> Iterable[str]:
        return {
            self._site.static_url_generator.generate('maps.css'),
        }

    @property
    def js_paths(self) -> Iterable[str]:
        return {
            self._site.static_url_generator.generate('maps.js'),
        }
