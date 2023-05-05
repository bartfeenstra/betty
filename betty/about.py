from os import path


def version() -> str:
    with open(path.join(path.dirname(__file__), 'assets', 'VERSION')) as f:
        release_version = f.read().strip()
    if release_version == '0.0.0':
        return 'development'
    return release_version
