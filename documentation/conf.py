import sys
from os import path

import betty
from betty import about

sys.path.insert(0, path.dirname(path.dirname(betty.__file__)))
project = 'Betty'
version = about.version() or ''
release = about.version_label()
html_favicon = 'betty.ico'
html_logo = 'betty-logo.png'
html_theme = 'sphinx_rtd_theme'
html_theme_options = {
    'collapse_navigation': True,
    'sticky_navigation': True,
    # 'navigation_depth': 1,
}
highlight_language = 'none'
templates_path = ['_templates']
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx_autodoc_typehints',
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
