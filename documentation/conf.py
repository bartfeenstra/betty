"""
Sphinx configuration.
"""

import sys
from pathlib import Path

import betty.dirs
from betty.dirs import ASSETS_DIRECTORY_PATH, ROOT_DIRECTORY_PATH

sys.path.insert(0, str(Path(betty.__file__).parent.parent))
project = "Betty"
copyright = "Bart Feenstra and contributors"  # noqa A001
intersphinx_mapping = {
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
    "babel": ("https://babel.pocoo.org/en/stable/", None),
    "geopy": ("https://geopy.readthedocs.io/en/stable/", None),
    "jinja2": ("https://jinja.palletsprojects.com/en/latest/", None),
    "jsonschema": ("https://python-jsonschema.readthedocs.io/en/stable/", None),
    "markupsafe": ("https://markupsafe.palletsprojects.com/en/latest/", None),
    "pillow": ("https://pillow.readthedocs.io/en/stable/", None),
    "polib": ("https://polib.readthedocs.io/en/latest/", None),
    "python": ("https://docs.python.org/3/", None),
    "referencing": ("https://referencing.readthedocs.io/en/stable/", None),
}
html_favicon = str(ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png")
html_logo = str(ASSETS_DIRECTORY_PATH / "public" / "static" / "betty-512x512.png")
html_context = {
    "display_github": True,
    "github_user": "bartfeenstra",
    "github_repo": "betty",
    "github_version": "0.5.x",
    "conf_py_path": "/documentation/",
}
html_theme = "shibuya"
html_theme_options = {
    "accent_color": "pink",
}
highlight_language = "none"
templates_path = ["_templates"]
extensions = [
    "sphinx.ext.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_design",
    "betty.sphinx.extension.betty",
]
modindex_common_prefix = ["betty."]
collapse_navigation = True
suppress_warnings = [
    # apidoc automatically inserts references that cannot be resolved.
    "ref.python",
]

# sphinx.ext.apidoc configuration.
apidoc_max_depth = 1
apidoc_separate_modules = True
apidoc_modules = [
    {
        "path": str(ROOT_DIRECTORY_PATH / "betty"),
        "destination": "api",
    }
]
apidoc_exclude_patterns = [
    str(ROOT_DIRECTORY_PATH / "betty" / "tests"),
]

# sphinx.ext.autodoc configuration.
autodoc_class_signature = "separated"
autodoc_member_order = "alphabetical"
