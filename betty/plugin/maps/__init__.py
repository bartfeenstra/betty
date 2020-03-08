from os.path import dirname
from typing import Optional, Set, Type

from betty.plugin import Plugin
from betty.plugin.js import Js, JsEntryPointProvider, JsPackageProvider


class Maps(Plugin, JsPackageProvider, JsEntryPointProvider):
    @classmethod
    def depends_on(cls) -> Set[Type[Plugin]]:
        return {Js}

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)
