import platform
import sys
from importlib.metadata import distributions
from pathlib import Path
from typing import Dict, Iterator


def version() -> str:
    with open(Path(__file__).parents[1] / 'VERSION', encoding='utf-8') as f:
        release_version = f.read().strip()
    if release_version == '0.0.0':
        return 'development'
    return release_version


def _indent_mapping(items: Dict[str, str]) -> str:
    max_indentation = max(map(len, items.keys())) + 4
    return '\n'.join(map(lambda x: '\n'.join(_indent_mapping_item(x[0], x[1], max_indentation)), items.items()))


def _indent_mapping_item(key: str, value: str, max_indentation: int) -> Iterator[str]:
    lines = value.split('\n')
    yield f'{key}{" " * (max_indentation - len(key))}    {lines[0]}'
    for line in lines[1:]:
        yield f'{" " * max_indentation}    {line}'


def report() -> str:
    return _indent_mapping({
        'Betty': version(),
        'Operating system': platform.platform(),
        'Python': sys.version,
        'Python packages': _indent_mapping({
            x.metadata["Name"]: x.version for x in sorted(distributions(), key=lambda x: x.metadata["Name"].lower())
        }),
    })
