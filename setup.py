"""Integrates Betty with Python's setuptools."""

from setuptools import setup

from betty import _ROOT_DIRECTORY_PATH as ROOT_DIRECTORY_PATH
from betty._package import get_data_paths, find_packages

with open(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'VERSION', encoding='utf-8') as f:
    VERSION = f.read()

with open(ROOT_DIRECTORY_PATH / 'README.md', encoding='utf-8') as f:
    long_description = f.read()

SETUP = {
    'name': 'betty',
    'description': 'Betty helps you visualize and publish your family history by building interactive genealogy websites out of your Gramps and GECOM family trees',
    'long_description': long_description,
    'long_description_content_type': 'text/markdown',
    'version': VERSION,
    'license': 'GPLv3',
    'author': 'Bart Feenstra & contributors',
    'author_email': 'bart@mynameisbart.com',
    'url': 'https://github.com/bartfeenstra/betty',
    'classifiers': [
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: JavaScript',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: JavaScript',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Internet',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Sociology :: Genealogy',
        'Topic :: Software Development :: Code Generators',
        'Natural Language :: Dutch',
        'Natural Language :: English',
        'Natural Language :: French',
        'Natural Language :: Ukrainian',
        'Typing :: Typed ',
    ],
    'python_requires': '~= 3.8',
    'install_requires': [
        'aiofiles ~= 23.1, >= 23.1.0',
        'aiohttp ~= 3.8, >= 3.8.1',
        'babel ~= 2.12, >= 2.12.0',
        'click ~= 8.1, >= 8.1.2',
        'geopy ~= 2.3, >= 2.3.0',
        'graphlib-backport ~= 1.0, >= 1.0.3; python_version < "3.9"',
        'jinja2 ~= 3.1, >= 3.1.1',
        'jsonschema ~= 4.17, >= 4.17.0',
        'markupsafe ~= 2.1, >= 2.1.1',
        'pdf2image ~= 1.16, >= 1.16.0',
        'polib ~= 1.2, >= 1.2.0',
        'Pillow ~= 9.5, >= 9.5.0',
        'PyQt6 ~= 6.5, >= 6.5.0',
        'pyyaml ~= 6.0, >= 6.0.0',
        'reactives ~= 0.5, >= 0.5.1',
        'typing_extensions ~= 4.5, >= 4.5.0; python_version < "3.11"',
    ],
    'extras_require': {
        'development': [
            'aioresponses ~= 0.7, >= 0.7.3',
            'autopep8 ~= 2.0, >= 2.0.2',
            'codecov ~= 2.1, >= 2.1.12',
            'coverage ~= 7.2, >= 7.2.4',
            'flake8 ~= 6.0, >= 6.0.0',
            'html5lib ~= 1.1',
            'lxml ~= 4.9, >= 4.9.1; sys.platform != "win32"',
            'mypy ~= 1.2, >= 1.2.0',
            'pip-licenses ~= 4.3, >= 4.3.0',
            'pyinstaller ~= 5.0',
            'pytest ~= 7.3, >= 7.3.1',
            'pytest-aioresponses ~= 0.2, >= 0.2.0 ',
            'pytest-asyncio ~= 0.21, >= 0.21.0 ',
            'pytest-cov ~= 4.0, >= 4.0.0',
            'pytest-mock ~= 3.10, >= 3.10.0',
            'pytest-qt ~= 4.2, >= 4.2.0',
            'pytest-xvfb ~= 2.0, >= 2.0.0',
            'setuptools ~= 67.7, >= 67.7.2',
            'twine ~= 4.0, >= 4.0.0',
            'types-aiofiles ~= 23.1, >= 23.1.0.2',
            'types-mock ~= 5.0, >= 5.0.0.6',
            'types-polib ~= 1.2, >= 1.2.0.0',
            'types-pyyaml ~= 6.0, >= 6.0.6',
            'types-requests ~= 2.29, >= 2.29.0.0',
            'types-setuptools ~= 67.7, >= 67.7.0.0',
            'wheel ~= 0.40, >= 0.40.0',
        ],
    },
    'entry_points': {
        'console_scripts': [
            'betty=betty.cli:main',
        ],
        'betty.extensions': [
            'betty.anonymizer.Anonymizer=betty.anonymizer.Anonymizer',
            'betty.cleaner.Cleaner=betty.cleaner.Cleaner',
            'betty.cotton_candy.CottonCandy=betty.cotton_candy.CottonCandy',
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
    'package_data': {
        'betty': list(map(str, data_file_paths))
        for package, data_file_paths
        in get_data_paths().items()
    },
}

if __name__ == '__main__':
    setup(**SETUP)
