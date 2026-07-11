"""
Utilities for testing Jinja2 templates.
"""

from __future__ import annotations

from json import loads
from typing import TYPE_CHECKING

from lxml.etree import ParserError
from lxml.html import document_fromstring

from betty.file import read
from betty.json_schema import embed_json_schema, validate
from betty.json_schemas.project import new_project_schema

if TYPE_CHECKING:
    from pathlib import Path

    from betty.project import Project


async def assert_betty_html(project: Project, url_path: str) -> Path:
    """
    Assert that an entity's HTML resource exists and is valid.
    """
    betty_html_file = project.www_directory / url_path.lstrip("/")
    betty_html = await read(betty_html_file)
    try:
        document_fromstring(betty_html)
    except ParserError as e:
        raise ValueError(
            f'HTML parse error "{e}" in:\n{betty_html}'
        ) from None  # pragma: no cover
    return betty_html_file


async def assert_betty_json(project: Project, url_path: str, def_name: str) -> Path:
    """
    Assert that an entity's JSON resource exists and is valid.
    """
    betty_json_file = project.www_directory / url_path.lstrip("/")
    betty_json = loads(await read(betty_json_file))
    defs = {}
    project_schema = await new_project_schema(project)
    embed_json_schema(project_schema, defs=defs)
    validate(
        {
            # Somehow $ref cannot be top-level in our case, so wrap it.
            "allOf": [
                {
                    "$ref": f"#/$defs/{def_name}",
                }
            ],
            "$defs": defs,
        },
        betty_json,
    )
    return betty_json_file
