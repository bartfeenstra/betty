"""Integrates Betty with Python's setuptools."""

from setuptools import setup

from betty import _ROOT_DIRECTORY_PATH as ROOT_DIRECTORY_PATH
from betty._package import get_data_paths, find_packages

with open(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'VERSION', encoding='utf-8') as f:
    VERSION = f.read()

with open(ROOT_DIRECTORY_PATH / 'README.md', encoding='utf-8') as f:
    long_description = f.read()


extras_require_pyinstaller = [
    'pyinstaller ~= 6.1, >= 6.1.0',
]


extras_require_setuptools = [
    'setuptools ~= 68.2, >= 68.2.2',
    'twine ~= 4.0, >= 4.0.0',
    'wheel ~= 0.40, >= 0.40.0',
]


extras_require_development = [
    'aioresponses ~= 0.7, >= 0.7.6',
    'autopep8 ~= 2.0, >= 2.0.2',
    'basedmypy ~= 2.0, >= 2.2.1',
    'codecov ~= 2.1, >= 2.1.12',
    'coverage ~= 7.2, >= 7.2.4',
    'flake8 ~= 6.0, >= 6.0.0',
    'html5lib ~= 1.1',
    'lxml ~= 4.9, >= 4.9.1; sys.platform != "win32"',
    'pip-licenses ~= 4.3, >= 4.3.0',
    'pytest ~= 7.3, >= 7.3.1',
    'pytest-aioresponses ~= 0.2, >= 0.2.0 ',
    'pytest-asyncio ~= 0.21, >= 0.21.0 ',
    'pytest-cov ~= 4.0, >= 4.0.0',
    'pytest-mock ~= 3.10, >= 3.10.0',
    'pytest-qt ~= 4.2, >= 4.2.0',
    'pytest-repeat ~= 0.9, >= 0.9.1',
    'pytest-xvfb ~= 3.0, >= 3.0.0',
    'types-aiofiles ~= 23.2, >= 23.2.0.0',
    'types-click ~= 7.1, >= 7.1.8',
    'types-mock ~= 5.0, >= 5.0.0.6',
    'types-polib ~= 1.2, >= 1.2.0.0',
    'types-pyyaml ~= 6.0, >= 6.0.6',
    'types-requests ~= 2.29, >= 2.29.0.0',
    'types-setuptools ~= 68.2, >= 68.2.0.0',
    *extras_require_pyinstaller,
    *extras_require_setuptools,
]


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
    'project_urls': {
        'Github': 'https://github.com/bartfeenstra/betty',
        'Twitter': 'https://twitter.com/BettyProject',
        'X': 'https://twitter.com/BettyProject',
    },
    'classifiers': [
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: JavaScript',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
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
    'python_requires': '~= 3.11',
    'install_requires': [
        'aiofiles ~= 23.2, >= 23.2.1',
        'aiohttp ~= 3.9',
        'babel ~= 2.12, >= 2.12.0',
        'click ~= 8.1, >= 8.1.2',
        'dill ~= 0.3, >= 0.3.6',
        'docker ~= 7.0, >= 7.0.0',
        'geopy ~= 2.3, >= 2.3.0',
        'jinja2 ~= 3.1, >= 3.1.1',
        'jsonschema ~= 4.17, >= 4.17.0',
        'langcodes ~= 3.3, >= 3.3.0',
        'markupsafe ~= 2.1, >= 2.1.1',
        'ordered-set ~= 4.1.0',
        'pdf2image ~= 1.16, >= 1.16.0',
        'polib ~= 1.2, >= 1.2.0',
        'Pillow ~= 10.1, >= 10.1.0',
        'PyQt6 ~= 6.5, >= 6.5.0',
        'pyyaml ~= 6.0, >= 6.0.0',
        'reactives ~= 0.5, >= 0.5.1',
    ],
    'extras_require': {
        'development': extras_require_development,
        'pyinstaller': extras_require_pyinstaller,
        'setuptools': extras_require_setuptools,
    },
    'entry_points': {
        'console_scripts': [
            'betty=betty.cli:main',
        ],
        'betty.extensions': [
            'betty.extension.CottonCandy=betty.extension.CottonCandy',
            'betty.extension.Demo=betty.extension.Demo',
            'betty.extension.Deriver=betty.extension.Deriver',
            'betty.extension.Gramps=betty.extension.Gramps',
            'betty.extension.Maps=betty.extension.Maps',
            'betty.extension.Privatizer=betty.extension.Privatizer',
            'betty.extension.HttpApiDoc=betty.extension.HttpApiDoc',
            'betty.extension.Trees=betty.extension.Trees',
            'betty.extension.Wikipedia=betty.extension.Wikipedia',
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
