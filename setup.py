"""Integrates Betty with Python's setuptools."""

from setuptools import setup, find_packages

from betty import _ROOT_DIRECTORY_PATH as ROOT_DIRECTORY_PATH
from betty._package import get_data_paths

with open(ROOT_DIRECTORY_PATH / 'VERSION', encoding='utf-8') as f:
    VERSION = f.read()

with open(ROOT_DIRECTORY_PATH / 'README.md', encoding='utf-8') as f:
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
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
    'python_requires': '~= 3.8',
    'install_requires': [
        'aiofiles ~= 0.8.0',
        'aiohttp ~= 3.8.1',
        'babel ~= 2.9.1',
        'click ~= 8.0.3',
        'geopy ~= 2.2.0',
        'graphlib-backport ~= 1.0; python_version < "3.9"',
        # This is a loose constraint because of conflicts between click 8.0.3 and flake8 4.0.1.
        'importlib-metadata ~= 4.0',
        'jinja2 ~= 3.0.1',
        'jsonschema ~= 4.4.0',
        'markupsafe ~= 2.0.1',
        'orderedset ~= 2.0.3',
        'pdf2image ~= 1.16.0',
        'PyQt6 ~= 6.2.3',
        'python-resize-image ~= 1.1.20',
        'pyyaml ~= 6.0.0',
        'reactives ~= 0.4.1',
    ],
    'extras_require': {
        'development': [
            'aioresponses ~= 0.7.3',
            'autopep8 ~= 1.6.0',
            'codecov ~= 2.1.12',
            'coverage ~= 6.3',
            'flake8 ~= 4.0.1',
            'html5lib ~= 1.1',
            'lxml ~= 4.7.1',
            'nose2 ~= 0.10',
            'mypy ~= 0.942',
            'parameterized ~= 0.8.1',
            'pip-licenses ~= 3.5.3',
            'pyinstaller ~= 4.8',
            'pytest ~= 6.2.2',
            'pytest-cov ~= 3.0.0',
            'pytest-mock ~= 3.7.0',
            'pytest-qt ~= 4.0.1',
            'pytest-xvfb ~= 2.0.0',
            'setuptools ~= 57.0.0',
            'twine ~= 3.7.1',
            'types-aiofiles ~= 0.8.4',
            'types-mock ~= 4.0.11',
            'types-pyyaml ~= 6.0.4',
            'types-requests ~= 2.27.12',
            'types-setuptools ~= 57.4.10',
            'wheel ~= 0.36',
        ],
    },
    'entry_points': {
        'console_scripts': [
            'betty=betty.cli:main',
        ],
        'betty.extensions': [
            'betty.anonymizer.Anonymizer=betty.anonymizer.Anonymizer',
            'betty.cleaner.Cleaner=betty.cleaner.Cleaner',
            'betty.demo.Demo=betty.demo.Demo',
            'betty.deriver.Deriver=betty.deriver.Deriver',
            'betty.gramps.Gramps=betty.gramps.Gramps',
            'betty.maps.Maps=betty.maps.Maps',
            'betty.privatizer.Privatizer=betty.privatizer.Privatizer',
            'betty.http_api_doc.HttpApiDoc=betty.http_api_doc.HttpApiDoc',
            'betty.trees.Trees=betty.trees.Trees',
            'betty.wikipedia.Wikipedia=betty.wikipedia.Wikipedia',
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
        'betty': list(map(str, get_data_paths()))
    },
}

if __name__ == '__main__':
    setup(**SETUP)
