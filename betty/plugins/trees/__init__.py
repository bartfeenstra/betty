from os.path import dirname

from betty.plugin import Plugin
from betty.plugins.js import Js, JsEntryPointProvider, JsPackageProvider


class Trees(Plugin, JsPackageProvider, JsEntryPointProvider):
    @classmethod
    def depends_on(cls):
        return {Js}

    @property
    def package_directory_path(self) -> str:
        return '%s/js' % dirname(__file__)
