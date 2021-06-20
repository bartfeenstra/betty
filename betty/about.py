from pathlib import Path


def version() -> str:
    with open(Path(__file__).parents[1] / 'VERSION') as f:
        release_version = f.read().strip()
    if release_version == '0.0.0':
        return 'development'
    return release_version
