from os.path import dirname
from typing import Optional

from betty.plugin import Plugin
from betty.plugins.npm import Npm, WebpackEntryPointProvider, NpmPackageProvider


class Maps(Plugin, NpmPackageProvider, WebpackEntryPointProvider):
    @classmethod
    def depends_on(cls):
        return {Npm}

    @property
    def resource_directory_path(self) -> Optional[str]:
        return '%s/resources' % dirname(__file__)
