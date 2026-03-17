"""
Utilities for testing Jinja2 templates.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
from lxml.etree import ParserError
from lxml.html import document_fromstring

from betty.json.schema import AllOf, Ref
from betty.project.schema import ProjectSchema

if TYPE_CHECKING:
    from betty.project import Project


async def assert_betty_html(project: Project, url_path: str) -> Path:
    """
    Assert that an entity's HTML resource exists and is valid.
    """
    betty_html_file_path = project.www_directory / Path(url_path.lstrip("/"))
    async with aiofiles.open(betty_html_file_path) as f:
        betty_html = await f.read()
    try:
        document_fromstring(betty_html)
    except ParserError as e:
        raise ValueError(
            f'HTML parse error "{e}" in:\n{betty_html}'
        ) from None  # pragma: no cover

    return betty_html_file_path


async def assert_betty_json(project: Project, url_path: str, def_name: str) -> Path:
    """
    Assert that an entity's JSON resource exists and is valid.
    """
    import json

    betty_json_file_path = project.www_directory / Path(url_path.lstrip("/"))
    async with aiofiles.open(betty_json_file_path) as f:
        betty_json = await f.read()
    betty_json_data = json.loads(betty_json)

    project_schema = await ProjectSchema.new(project)
    # Somehow $ref cannot be top-level in our case, so wrap it.
    schema = AllOf(Ref(def_name))
    project_schema.embed(schema)

    schema.validate(betty_json_data)

    return betty_json_file_path
