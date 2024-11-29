"""
Provide Sphinx configuration.
"""

import sys
from asyncio import run
from pathlib import Path

import betty
from betty import fs
from betty.assets import AssetRepository
from betty.fs import ASSETS_DIRECTORY_PATH
from betty.locale.localizer import LocalizerRepository

betty_replacements: dict[str, str] = {}

assets = AssetRepository(fs.ASSETS_DIRECTORY_PATH)
localizers = LocalizerRepository(assets)
for locale in localizers.locales:
    coverage = run(localizers.coverage(locale))
    betty_replacements[f"translation-coverage-{locale}"] = str(
        int(round(100 / (coverage[1] / coverage[0]) if coverage[0] else 0))
    )

sys.path.insert(0, str(Path(betty.__file__).parent.parent))
project = "Betty"
copyright = "Bart Feenstra and contributors"  # noqa A001
intersphinx_mapping = {
    "aiohttp": ("https://docs.aiohttp.org/en/stable/", None),
    "babel": ("https://babel.pocoo.org/en/stable/", None),
    "click": ("https://click.palletsprojects.com/en/latest/", None),
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
    "github_version": "0.4.x",
    "conf_py_path": "/documentation/",
    "betty_replacements": betty_replacements,
}
html_theme = "furo"
highlight_language = "none"
templates_path = ["_templates"]
extensions = [
    "betty.sphinx.extension.replacements",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx_design",
]
nitpicky = True
modindex_common_prefix = ["betty."]
collapse_navigation = True

# sphinx.ext.autodoc configuration.
autodoc_class_signature = "separated"
autodoc_member_order = "alphabetical"
