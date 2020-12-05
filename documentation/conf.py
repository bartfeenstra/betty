import os
from gettext import NullTranslations
from os import path
import sys

import betty
from betty import about
from betty.locale import Translations

sys.path.insert(0, path.dirname(path.dirname(betty.__file__)))
project = 'Betty'
with Translations(NullTranslations()):
    copyright = about.copyright_details()
    author = about.authors()
version = '%d.%d' % (about.version().major, about.version().minor) if about.version() else ''
release = about. version_label()
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 1,
}
highlight_language = 'none'
templates_path = ['_templates']
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    # Load sphinx.ext.napoleon before sphinx_autodoc_typehints. See
    # https://github.com/agronholm/sphinx-autodoc-typehints/issues/15.
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
]

# sphinx.ext.autodoc configuration.
autodoc_member_order = 'alphabetical'
autodoc_default_options = {
    'members': None,
    'undoc-members': None,
    'show-inheritnace': None,
}

# sphinx.ext.napoleon configuration.
napoleon_google_docstring = False
napoleon_numpy_docstring = True

# sphinx_autodoc_typehints configuration.
set_type_checking_flag = True
typehints_fully_qualified = True
always_document_param_types = True

# Betty templating.
if 'BETTY_AVAILABLE_VERSIONS' in os.environ:
    _available_versions_and_urls = os.environ['BETTY_AVAILABLE_VERSIONS'].split()
    available_versions_and_urls = []
    for _available_version_and_url in _available_versions_and_urls:
        available_versions_and_urls.append(tuple(_available_version_and_url.split(';', 1)))
else:
    available_versions_and_urls = []
html_context = {
    'betty_current_version': version,
    'betty_available_versions_and_urls': available_versions_and_urls,
}
