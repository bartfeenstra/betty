"""
Provide Sphinx configuration.
"""

import sys
from pathlib import Path

import betty
from betty import about, fs
from betty.asyncio import wait_to_thread
from betty.fs import ROOT_DIRECTORY_PATH, FileSystem
from betty.locale import LocalizerRepository

betty_replacements: dict[str, str] = {}

assets = FileSystem()
assets.prepend(fs.ASSETS_DIRECTORY_PATH, "utf-8")
localizers = LocalizerRepository(assets)
for locale in localizers.locales:
    coverage = wait_to_thread(localizers.coverage(locale))
    betty_replacements[f"translation-coverage-{locale}"] = str(
        int(round(100 / (coverage[1] / coverage[0])))
    )

sys.path.insert(0, str(Path(betty.__file__).parent.parent))
project = "Betty"
version = wait_to_thread(about.version()) or ""
release = wait_to_thread(about.version_label())
copyright = "Bart Feenstra and contributors"  # noqa A001
intersphinx_mapping = {
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
    "babel": ("https://babel.pocoo.org/en/stable/", None),
    "click": ("https://click.palletsprojects.com/en/latest/", None),
    "docker": ("https://docker-py.readthedocs.io/en/stable/", None),
    "geopy": ("https://geopy.readthedocs.io/en/stable/", None),
    "jinja2": ("https://jinja.palletsprojects.com/en/latest/", None),
    "jsonschema": ("https://python-jsonschema.readthedocs.io/en/stable/", None),
    "markupsafe": ("https://markupsafe.palletsprojects.com/en/latest/", None),
    "pillow": ("https://pillow.readthedocs.io/en/stable/", None),
    "polib": ("https://polib.readthedocs.io/en/latest/", None),
    "python": ("https://docs.python.org/3/", None),
    "referencing": ("https://referencing.readthedocs.io/en/stable/", None),
}
html_favicon = str(
    ROOT_DIRECTORY_PATH / "betty" / "assets" / "public" / "static" / "betty.ico"
)
html_logo = str(
    ROOT_DIRECTORY_PATH / "betty" / "assets" / "public" / "static" / "betty-32x32.png"
)
html_context = {
    "display_github": True,
    "github_user": "bartfeenstra",
    "github_repo": "betty",
    "github_version": "0.3.x",
    "conf_py_path": "/documentation/",
    "betty_replacements": betty_replacements,
}
html_theme = "sphinx_immaterial"
highlight_language = "none"
templates_path = ["_templates"]
extensions = [
    "betty.sphinx.extension.replacements",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_autodoc_typehints",
    "sphinx_design",
    "sphinx_immaterial",
]
nitpicky = True
modindex_common_prefix = ["betty."]

# sphinx.ext.autodoc configuration.
autodoc_member_order = "alphabetical"

# sphinx_autodoc_typehints configuration.
set_type_checking_flag = True
typehints_fully_qualified = True
always_document_param_types = True
