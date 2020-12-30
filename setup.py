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
        'Programming Language :: JavaScript',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Sociology :: Genealogy',
        'Topic :: Software Development :: Code Generators',
        'Natural Language :: Dutch',
        'Natural Language :: English',
        'Natural Language :: Ukrainian',
    ],
    'python_requires': '~= 3.6',
    'install_requires': [
        'aiohttp ~= 3.7',
        'async-exit-stack ~= 1.0; python_version <= "3.6"',
        'async_generator ~= 1.10; python_version <= "3.6"',
        'babel ~= 2.9',
        'click ~= 7.1',
        'docker ~= 4.4',
        'geopy ~= 2.0',
        'jinja2 ~= 2.11',
        'jsonschema ~= 3.2',
        'libsass ~= 0.20',
        'markupsafe ~= 1.1',
        'pdf2image ~= 1.14 ',
        'python-resize-image ~= 1.1',
        'pyyaml ~= 5.3',
        'voluptuous ~= 0.12',
    ],
    'extras_require': {
        'development': [
            'aioresponses ~= 0.7',
            'autopep8 ~= 1.5',
            'codecov ~= 2.1',
            'coverage ~= 5.3',
            # flake8 3.8 fails on circular imports caused by string-based type hints.
            'flake8 ~= 3.7.0',
            'html5lib ~= 1.1',
            'mock ~= 4.0; python_version <= "3.7"',
            'lxml ~= 4.6',
            'nose2 ~= 0.9',
            'parameterized ~= 0.7',
            'setuptools ~= 50.3',
            'twine ~= 3.2',
            'wheel ~= 0.36',
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
        'betty': [
                     join(dirname(__file__), 'VERSION'),
                 ]
                 +
                 glob(join(dirname(abspath(__file__)), 'betty', 'assets', '**'), recursive=True)
                 +
                 glob(join(dirname(abspath(__file__)), 'betty', 'plugin', '*', 'assets', '**'), recursive=True),
    },
}

if __name__ == '__main__':
    setup(**SETUP)
