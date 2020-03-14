from os.path import dirname
from typing import Optional, Type, Set

from betty.plugin import Plugin
from betty.plugin.npm import Npm, WebpackEntryPointProvider, NpmPackageProvider


class Trees(Plugin, NpmPackageProvider, WebpackEntryPointProvider):
    @classmethod
    def depends_on(cls) -> Set[Type[Plugin]]:
        return {Npm}

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)
