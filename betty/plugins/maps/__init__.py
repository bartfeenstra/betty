from os.path import dirname
from typing import Optional

from betty.plugin import Plugin
from betty.plugins.js import Js, JsEntryPointProvider, JsPackageProvider


class Maps(Plugin, JsPackageProvider, JsEntryPointProvider):
    @classmethod
    def depends_on(cls):
        return {Js}

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)
