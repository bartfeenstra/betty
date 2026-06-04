"""
Sphinx configuration.
"""

import sys
from pathlib import Path

import betty.dirs
from betty.about import version_major
from betty.dirs import builtin_asset_directory, root_directory

sys.path.insert(0, str(Path(betty.__file__).parent.parent))
project = "Betty"
copyright = "Bart Feenstra and contributors"  # noqa: A001
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
html_favicon = str(builtin_asset_directory / "public" / "static" / "betty-512x512.png")
html_logo = str(builtin_asset_directory / "public" / "static" / "betty-512x512.png")
html_theme = "shibuya"
html_theme_options = {
    "accent_color": "pink",
}
html_context = {
    "source_edit_template": f"https://github.com/bartfeenstra/betty/blob/{version_major}.x/{{0}}",
    "source_type": "github",
    "source_user": "bartfeenstra",
    "source_version": version_major + "x",
    "source_repo": "betty",
}
highlight_language = "none"
templates_path = ["_templates"]
extensions = [
    "sphinx.ext.apidoc",
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
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
        "path": str(root_directory / "betty"),
        "destination": "api",
    }
]
apidoc_exclude_patterns = [
    str(root_directory / "betty" / "tests"),
]

# sphinx.ext.autodoc configuration.
autodoc_class_signature = "separated"
autodoc_member_order = "alphabetical"
