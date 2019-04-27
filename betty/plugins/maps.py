import hashlib
from os import makedirs
from os.path import join, expanduser
from shutil import copy2
from subprocess import Popen

import betty
from betty import RESOURCE_PATH
from betty.event import POST_RENDER_EVENT
from betty.plugin import Plugin
from betty.plugins.npm import NpmPlugin

_BETTY_INSTANCE_ID = hashlib.sha1(betty.__path__[0].encode()).hexdigest()
BETTY_INSTANCE_NPM_DIR = join(expanduser('~'), '.betty', _BETTY_INSTANCE_ID)


class MapsPlugin(Plugin):
    @classmethod
    def depends_on(cls):
        return {NpmPlugin}

    def subscribes_to(self):
        return {
            (POST_RENDER_EVENT, self.install),
        }

    def install(self, dev: bool = False) -> None:
        self._ensure_target()
        args = ['npm', 'install']
        if not dev:
            args.append('--production')
        Popen(args, cwd=BETTY_INSTANCE_NPM_DIR).wait()

    def _ensure_target(self) -> None:
        makedirs(BETTY_INSTANCE_NPM_DIR, 0o700, True)
        files = ['package.json', 'webpack.config.js']
        for file in files:
            copy2(join(RESOURCE_PATH, file), join(
                BETTY_INSTANCE_NPM_DIR, file))
