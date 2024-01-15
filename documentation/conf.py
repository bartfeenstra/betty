import sys
from os import path

import betty
from betty import about
from betty.fs import ROOT_DIRECTORY_PATH

sys.path.insert(0, path.dirname(path.dirname(betty.__file__)))
project = 'Betty'
version = about.version() or ''
release = about.version_label()
copyright = 'Bart Feenstra and contributors'
html_favicon = str(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'public' / 'static' / 'betty.ico')
html_logo = str(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'public' / 'static' / 'betty-32x32.png')
html_context = {
    'display_github': True,
    'github_user': 'bartfeenstra',
    'github_repo': 'betty',
    'github_version': '0.3.x',
    'conf_py_path': '/documentation/',
}
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'collapse_navigation': True,
    'sticky_navigation': True,
    'prev_next_buttons_location': None,
}
html_css_files = [
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
]
highlight_language = 'none'
templates_path = ['_templates']
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
    'sphinx_design',
]
nitpicky = True
modindex_common_prefix = ['betty.']

# sphinx.ext.autodoc configuration.
autodoc_member_order = 'alphabetical'
autodoc_default_options = {
    'members': None,
    'undoc-members': None,
    'show-inheritnace': None,
}

# sphinx_autodoc_typehints configuration.
set_type_checking_flag = True
typehints_fully_qualified = True
always_document_param_types = True
