from os.path import dirname, join
from shutil import copytree
from typing import Tuple, Callable, List, Dict

from betty.event import POST_RENDER_EVENT
from betty.plugin import Plugin
from betty.plugins.js import Js, JsEntryPointProvider, JsPackageProvider
from betty.site import Site


class Maps(Plugin, JsPackageProvider, JsEntryPointProvider):
    def __init__(self, npm_directory_path: str, output_directory_path: str):
        self._npm_directory_path = npm_directory_path
        self._output_directory_path = output_directory_path

    @classmethod
    def from_configuration_dict(cls, site: Site, configuration: Dict):
        return cls(site.plugins[Js].directory_path, site.configuration.output_directory_path)

    @classmethod
    def depends_on(cls):
        return {Js}

    def subscribes_to(self) -> List[Tuple[str, Callable]]:
        return [
            (POST_RENDER_EVENT, lambda *_: self._copy_images()),
        ]

    def _copy_images(self):
        copytree(join(self._npm_directory_path, 'node_modules', 'leaflet', 'dist',
                      'images'), join(self._output_directory_path, 'images', 'leaflet'))

    @property
    def package_directory_path(self) -> str:
        return '%s/js' % dirname(__file__)

    @property
    def entry_point(self) -> Tuple[str, str]:
        return 'initializePlaceLists', 'maps.js'
