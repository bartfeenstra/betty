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

SETUP = {
    'name': 'betty',
    'description': 'Betty is a static ancestry site generator.',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'version': VERSION,
    'license': 'GPLv3',
    'author': 'Bart Feenstra',
    'url': 'https://github.com/bartfeenstra/betty',
    'classifiers': [
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: MacOS',
        'Operating System :: POSIX :: BSD',
        'Operating System :: POSIX :: Linux',
        'Operating System :: POSIX :: SunOS/Solaris',
        'Operating System :: Unix',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Sociology :: Genealogy',
        'Topic :: Software Development :: Code Generators',
    ],
    'install_requires': [
        'geopy ~= 1.18.1',
        'jinja2 ~= 2.10',
        'libsass ~= 0.19.2',
        'lxml ~= 4.3.1',
        'markupsafe ~= 1.1.1',
        'python-resize-image ~= 1.1.18',
        'pyyaml ~= 5.1.2',
        'voluptuous ~= 0.11.7',
    ],
    'extras_require': {
        'development': [
            'autopep8 ~= 1.4.3',
            'babel ~= 2.7.0',
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
            'LICENSE.txt',
            'README.md',
            'VERSION',
        ])
    ],
    'include_package_data': True,
    'package_data': {
        'betty': chain(
            iterfiles(join(dirname(abspath(__file__)), 'betty', 'resources')),
            iterfiles(join(dirname(abspath(__file__)), 'betty', 'plugins', 'js', 'js')),
            iterfiles(join(dirname(abspath(__file__)), 'betty', 'plugins', 'maps', 'js')),
        ),
    },
}

if __name__ == '__main__':
    setup(**SETUP)
