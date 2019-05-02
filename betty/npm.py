import hashlib
from os import makedirs
from os.path import join, expanduser
from subprocess import Popen

import betty
from betty import RESOURCE_PATH
from betty.render import _copytree

_BETTY_INSTANCE_ID = hashlib.sha1(betty.__path__[0].encode()).hexdigest()
BETTY_INSTANCE_NPM_DIR = join(expanduser('~'), '.betty', _BETTY_INSTANCE_ID)


def install(dev: bool = False) -> None:
    ensure_target()
    args = ['npm', 'install']
    if not dev:
        args.append('--production')
    Popen(args, cwd=BETTY_INSTANCE_NPM_DIR).wait()


def ensure_target() -> None:
    makedirs(BETTY_INSTANCE_NPM_DIR, 0o700, True)
    files = ['package.json', 'webpack.config.js']
    for file in files:
        _copytree(join(RESOURCE_PATH, file), join(
            BETTY_INSTANCE_NPM_DIR, file))
