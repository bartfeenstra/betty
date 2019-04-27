import hashlib
from os import makedirs
from os.path import join, expanduser
from shutil import copy2
from subprocess import Popen

import betty
from betty import RESOURCE_PATH
from betty.event import POST_RENDER_EVENT
from betty.plugin import Plugin


class NpmPlugin(Plugin):
    _BETTY_INSTANCE_ID = hashlib.sha1(betty.__path__[0].encode()).hexdigest()
    _BETTY_INSTANCE_NPM_DIR = join(expanduser('~'), '.betty', _BETTY_INSTANCE_ID)

    def subscribes_to(self):
        return {
            (POST_RENDER_EVENT, lambda *args: self._install()),
        }

    @property
    def dir(self):
        return self._BETTY_INSTANCE_NPM_DIR

    def _install(self, dev: bool = False) -> None:
        self._ensure_target()
        args = ['npm', 'install']
        if not dev:
            args.append('--production')
        Popen(args, cwd=self.dir).wait()

    def _ensure_target(self) -> None:
        makedirs(self.dir, 0o700, True)
        files = ['package.json', 'webpack.config.js']
        for file in files:
            copy2(join(RESOURCE_PATH, file), join(
                self.dir, file))
