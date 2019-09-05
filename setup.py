"""Integrates Betty with Python's setuptools."""

import os
from itertools import chain
from os.path import abspath, dirname, join

from setuptools import setup, find_packages

from betty.fs import iterfiles

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

with open('/'.join((ROOT_PATH, 'VERSION'))) as f:
    VERSION = f.read()

with open('/'.join((ROOT_PATH, 'README.md'))) as f:
    long_description = f.read()

try:
    from m2r import convert

    long_description = convert(long_description)
except ImportError:
    # Allow this to fail, because we cannot guarantee this dependency is installed.
    pass

SETUP = {
    'name': 'betty',
    'description': 'Betty is a static ancestry site generator.',
    'long_description': long_description,
    'version': VERSION,
    'license': 'GPLv3',
    'author': 'Bart Feenstra',
    'url': 'https://github.com/bartfeenstra/betty',
    'classifiers': [
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    'install_requires': [
        'geopy ~= 1.18.1',
        'jinja2 ~= 2.10',
        'jsonschema ~= 3.0',
        'lxml ~= 4.3.1',
        'markupsafe ~= 1.1.1',
        'python-resize-image ~= 1.1.18',
    ],
    'extras_require': {
        'development': [
            'autopep8 ~= 1.4.3',
            'codecov ~= 2.0.15',
            'coverage ~= 4.5',
            'flake8 ~= 3.7.0',
            'html5lib ~= 1.0.1',
            'nose2 ~= 0.8',
            'parameterized ~= 0.6',
            'recommonmark ~= 0.4.0',
            'requests-mock ~= 1.6.0',
            'twine ~= 1.9.1',
            'wheel ~= 0.30.0',
        ],
    },
    'entry_points': {
        'console_scripts': [
            'betty=betty.cli:main',
        ],
    },
    'packages': find_packages(),
    'data_files': [
        ('', [
            'LICENSE',
            'README.md',
            'VERSION',
        ])
    ],
    'include_package_data': True,
    'package_data': {
        'betty': chain(
            [join(dirname(abspath(__file__)), 'betty', 'config.schema.json')],
            iterfiles(join(dirname(abspath(__file__)), 'betty', 'resources')),
            iterfiles(join(dirname(abspath(__file__)), 'betty', 'plugins', 'js', 'js')),
            iterfiles(join(dirname(abspath(__file__)), 'betty', 'plugins', 'maps', 'js')),
        ),
    },
}

if __name__ == '__main__':
    setup(**SETUP)
