"""
Provide a Sphinx plugin to apply string replacements to source code.
"""

from collections.abc import MutableSequence

from sphinx.application import Sphinx


def render_replacements(
    app: Sphinx, docname: str, source: MutableSequence[str]
) -> None:
    """
    Handle Sphinx's source-read event to perform string replacements.
    """
    for token_name, value in app.env.config["html_context"][
        "betty_replacements"
    ].items():
        source[0] = source[0].replace("{{{ " + token_name + " }}}", value)


def setup(app: Sphinx) -> None:
    """
    Implement Sphinx's extension setup.
    """
    app.connect("source-read", render_replacements)
