import sys
from os import path

import betty
from betty import about, fs
from betty.asyncio import wait_to_thread
from betty.fs import ROOT_DIRECTORY_PATH, FileSystem
from betty.locale import LocalizerRepository

betty_replacements: dict[str, str] = {}

assets = FileSystem()
assets.prepend(fs.ASSETS_DIRECTORY_PATH, 'utf-8')
localizers = LocalizerRepository(assets)
for locale in localizers.locales:
    coverage = wait_to_thread(localizers.coverage(locale))
    betty_replacements[f'translation-coverage-{locale}'] = str(int(round(100 / (coverage[1] / coverage[0]))))

sys.path.insert(0, path.dirname(path.dirname(betty.__file__)))
project = 'Betty'
version = wait_to_thread(about.version()) or ''
release = wait_to_thread(about.version_label())
copyright = 'Bart Feenstra and contributors'
intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'jinja2': ('https://jinja.palletsprojects.com/en/latest/', None),
}
html_favicon = str(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'public' / 'static' / 'betty.ico')
html_logo = str(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'public' / 'static' / 'betty-32x32.png')
html_context = {
    'display_github': True,
    'github_user': 'bartfeenstra',
    'github_repo': 'betty',
    'github_version': '0.3.x',
    'conf_py_path': '/documentation/',
    'betty_replacements': betty_replacements,
}
html_theme = 'sphinx_immaterial'
highlight_language = 'none'
templates_path = ['_templates']
extensions = [
    'betty.sphinx.extension.replacements',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
    'sphinx_design',
    'sphinx_immaterial',
]
nitpicky = True
modindex_common_prefix = ['betty.']

# sphinx.ext.autodoc configuration.
autodoc_member_order = 'alphabetical'

# sphinx_autodoc_typehints configuration.
set_type_checking_flag = True
typehints_fully_qualified = True
always_document_param_types = True
