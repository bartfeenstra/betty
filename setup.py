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
    'author': 'Bart Feenstra & contributors',
    'author_email': 'bart@mynameisbart.com',
    'url': 'https://github.com/bartfeenstra/betty',
    'classifiers': [
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
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
        'aiohttp ~= 3.7.3',
        'async-exit-stack ~= 1.0.1; python_version <= "3.6"',
        'async_generator ~= 1.10; python_version <= "3.6"',
        'babel ~= 2.9.0',
        'click ~= 7.1.2',
        'docker ~= 4.3.1',
        'geopy ~= 2.0.0',
        'jinja2 ~= 2.11.2',
        'jsonschema ~= 3.2.0',
        'libsass ~= 0.20.1',
        'lxml ~= 4.6.1',
        'markupsafe ~= 1.1.1',
        'pdf2image ~= 1.14.0 ',
        'python-resize-image ~= 1.1.19',
        'pyyaml ~= 5.3.1',
        'voluptuous ~= 0.12.0',
    ],
    'extras_require': {
        'development': [
            'aioresponses ~= 0.7.1',
            'autopep8 ~= 1.5.4',
            'codecov ~= 2.1.10',
            'coverage ~= 5.3',
            'flake8 ~= 3.7.0',
            'html5lib ~= 1.1',
            'mock ~= 4.0.2; python_version <= "3.7"',
            'nose2 ~= 0.9.2',
            'parameterized ~= 0.7.4',
            'setuptools ~= 50.3.2',
            'twine ~= 3.2.0',
            'wheel ~= 0.35.1',
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
        'betty': glob(join(dirname(abspath(__file__)), 'betty', 'assets', '**'), recursive=True) + glob(join(dirname(abspath(__file__)), 'betty', 'plugin', '*', 'assets', '**'), recursive=True),
    },
}

if __name__ == '__main__':
    setup(**SETUP)
