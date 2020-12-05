from datetime import datetime
from os import path
from typing import Optional

from semver import VersionInfo


def version() -> Optional[VersionInfo]:
    with open(path.join(path.dirname(path.dirname(__file__)), 'VERSION')) as f:
        release_version = f.read().strip()
    if release_version == '':
        return None
    return VersionInfo.parse(release_version)


def version_label() -> str:
    return str(version()) if version() else 'development'


def authors() -> str:
    return _('{primary_author} & contributors').format(primary_author='Bart Feenstra')


def copyright_details() -> str:
    return _('2019-{current_year} {authors}').format(authors=authors(), current_year=datetime.now().year)


def copyright_message() -> str:
    return _('Copyright {copyright_details}').format(copyright_details=copyright_details())
