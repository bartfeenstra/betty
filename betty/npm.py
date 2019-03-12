import hashlib
from os import makedirs
from os.path import join, expanduser
from shutil import copy2
from subprocess import Popen, PIPE

import betty
from betty import RESOURCE_PATH

_BETTY_INSTANCE_ID = hashlib.sha1(betty.__path__[0].encode()).hexdigest()
_BETTY_INSTANCE_NPM_DIR = join(expanduser('~'), '.betty', _BETTY_INSTANCE_ID)


def install() -> None:
    ensure_target()
    p = Popen(['npm', 'install', '--only', 'prod'], cwd=_BETTY_INSTANCE_NPM_DIR,
              stdout=PIPE, stderr=PIPE)
    p.wait()


def ensure_target() -> None:
    makedirs(_BETTY_INSTANCE_NPM_DIR, 0o700, True)
    copy2(join(RESOURCE_PATH, 'package.json'), join(
        _BETTY_INSTANCE_NPM_DIR, 'package.json'))
