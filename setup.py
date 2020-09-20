"""Integrates Betty with Python's setuptools."""

import os
from glob import glob
from os.path import abspath, dirname, join

from setuptools import setup, find_packages

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
    'python_requires': '~= 3.6',
    'install_requires': [
        'aiohttp ~= 3.6.2',
        'async-exit-stack ~= 1.0.0; python_version <= "3.6"',
        'async_generator ~= 1.10; python_version <= "3.6"',
        'babel ~= 2.7.0',
        'click ~= 7.1.1',
        'geopy ~= 1.18.1',
        'jinja2 ~= 2.10',
        'jsonschema ~= 3.2.0',
        'libsass ~= 0.19.2',
        'lxml ~= 4.3.1',
        'markupsafe ~= 1.1.1',
        'orderedset ~= 2.0.3',
        'python-resize-image ~= 1.1.18',
        'pyyaml ~= 5.1.2',
        'voluptuous ~= 0.11.7',
    ],
    'extras_require': {
        'development': [
            'aioresponses ~= 0.6.3',
            'autopep8 ~= 1.4.3',
            'codecov ~= 2.0.15',
            'coverage ~= 4.5',
            'flake8 ~= 3.7.0',
            'html5lib ~= 1.0.1',
            'mock ~= 4.0.0; python_version <= "3.7"',
            'nose2 ~= 0.8',
            'parameterized ~= 0.6',
            'recommonmark ~= 0.4.0',
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
        'betty': glob(join(dirname(abspath(__file__)), 'betty', 'assets', '**'), recursive=True) + glob(join(dirname(abspath(__file__)), 'betty', 'plugins', '*', 'assets', '**'), recursive=True),
    },
}

if __name__ == '__main__':
    setup(**SETUP)
