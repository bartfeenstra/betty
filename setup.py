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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: JavaScript',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Sociology :: Genealogy',
        'Topic :: Software Development :: Code Generators',
        'Natural Language :: Dutch',
        'Natural Language :: English',
        'Natural Language :: French',
        'Natural Language :: Ukrainian',
    ],
    'python_requires': '~= 3.8',
    'install_requires': [
        'aiofiles ~= 22.1.0',
        'aiohttp ~= 3.8.1',
        'babel ~= 2.11.0',
        'click ~= 8.1.2',
        'geopy ~= 2.2.0',
        'graphlib-backport ~= 1.0.3; python_version < "3.9"',
        'jinja2 ~= 3.1.1',
        'jsonschema ~= 4.17.0',
        'markupsafe ~= 2.1.1',
        'pdf2image ~= 1.16.0',
        'polib ~= 1.1.1',
        'Pillow ~= 9.3.0',
        'PyQt6 ~= 6.4.0',
        'pyyaml ~= 6.0.0',
        # @todo Set this to ~= 0.5.0 once that version has been released.
        'reactives @ git+https://github.com/bartfeenstra/reactives.git@8df7478e39cc094b0cee86cb9945a8cb780b61b9',
        'typing_extensions ~= 4.4.0; python_version < "3.11"',
    ],
    'extras_require': {
        'development': [
            'aioresponses ~= 0.7.3',
            'autopep8 ~= 2.0.0',
            'codecov ~= 2.1.12',
            'coverage ~= 6.5.0',
            'flake8 ~= 5.0.4',
            'html5lib ~= 1.1',
            'lxml ~= 4.9.1; sys.platform != "win32"',
            # @todo Set this to ~= 0.992 (or whichever version comes after 0.991) once that version has been released.
            'mypy @ git+https://github.com/python/mypy.git@98cc165a657a316accb93f1ed57fdc128b086d9f',
            'pip-licenses ~= 4.0.0-rc3',
            'pyinstaller ~= 5.0',
            'pytest ~= 7.2.0',
            'pytest-aioresponses ~= 0.2.0 ',
            'pytest-asyncio ~= 0.20.1 ',
            'pytest-cov ~= 4.0.0',
            'pytest-mock ~= 3.10.0',
            'pytest-qt ~= 4.2.0',
            'pytest-xvfb ~= 2.0.0',
            'setuptools ~= 65.5.0',
            'twine ~= 4.0.0',
            'types-aiofiles ~= 22.1.0',
            'types-mock ~= 4.0.13',
            'types-polib ~= 1.1.12',
            'types-pyyaml ~= 6.0.6',
            'types-requests ~= 2.28.11.2',
            'types-setuptools ~= 65.5.0.2',
            'wheel ~= 0.37.1',
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
            *list(map(str, get_data_paths())),
            str(ROOT_DIRECTORY_PATH / 'betty' / 'py.typed'),
        ],
    },
}

if __name__ == '__main__':
    setup(**SETUP)
