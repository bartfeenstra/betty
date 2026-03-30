"""
Provide the HTML API, for generating HTML pages.
"""

from __future__ import annotations

import re
from uuid import uuid4

from markupsafe import escape

_paragraph_re = re.compile(r"(?:\r\n|\r|\n){2,}")


def newlines_to_paragraphs(text: str) -> str:
    """
    Convert newlines to <p> and <br> tags.
    """
    return "\n\n".join(
        "<p>{}</p>".format(paragraph.replace("\n", "<br>\n"))
        for paragraph in _paragraph_re.split(text)
    )


def plain_text_to_html(text: str) -> str:
    """
    Convert plain text to HTML.
    """
    return newlines_to_paragraphs(escape(text))


def generate_html_id() -> str:
    """
    Generate a unique HTML ID.
    """
    return f"betty-generated--{uuid4()}"
