import hashlib
from os import makedirs
from os.path import join, expanduser
from shutil import copy2
from subprocess import Popen

import betty
from betty import RESOURCE_PATH

_BETTY_INSTANCE_ID = hashlib.sha1(betty.__path__[0].encode()).hexdigest()
BETTY_INSTANCE_NPM_DIR = join(expanduser('~'), '.betty', _BETTY_INSTANCE_ID)


def install(only: str = 'prod') -> None:
    ensure_target()
    Popen(['npm', 'install', '--only=%s' % only],
          cwd=BETTY_INSTANCE_NPM_DIR).wait()


def ensure_target() -> None:
    makedirs(BETTY_INSTANCE_NPM_DIR, 0o700, True)
    copy2(join(RESOURCE_PATH, 'package.json'), join(
        BETTY_INSTANCE_NPM_DIR, 'package.json'))
