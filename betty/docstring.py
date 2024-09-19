"""
Providing docstring utilities.
"""

from __future__ import annotations

from textwrap import wrap


def append(docstring: str, *paragraphs: str) -> str:
    """
    Append paragraphs to a docstring.
    """
    indentation = ""
    docstring = docstring.rstrip()
    if docstring:
        if "\n" in docstring:
            indentations = []
            for line in docstring.split("\n")[1:]:
                if line.strip():
                    indentations.append(len(line) - len(line.lstrip()))
            if indentations:
                indentation = " " * min(indentations)
        docstring += "\n\n"
    else:
        docstring = ""
    docstring += "\n\n".join(
        [
            "\n".join(
                wrap(
                    paragraph, initial_indent=indentation, subsequent_indent=indentation
                )
            )
            for paragraph in paragraphs
        ]
    )
    return docstring.rstrip()
