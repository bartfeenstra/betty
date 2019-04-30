from os.path import dirname
from typing import Tuple

from betty.plugin import Plugin
from betty.plugins.js import Js, JsEntryPointProvider, JsPackageProvider


class Maps(Plugin, JsPackageProvider, JsEntryPointProvider):
    @classmethod
    def depends_on(cls):
        return {Js}

    @property
    def package_directory_path(self) -> str:
        return '%s/js' % dirname(__file__)

    @property
    def entry_point(self) -> Tuple[str, str]:
        return 'initializePlaceLists', 'maps.js'
