import json as stdjson
from pathlib import Path

import aiofiles
import jsonschema
import pytest

from betty.app import App
from betty.openapi import Specification
from betty.project import Project


class TestSpecification:
    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_build(self, clean_urls: bool, new_temporary_app: App) -> None:
        async with aiofiles.open(
            Path(__file__).parent / "test_openapi_assets" / "openapi-schema.json"
        ) as f:
            schema = stdjson.loads(await f.read())
        project = Project(new_temporary_app)
        project.configuration.clean_urls = clean_urls
        async with project:
            sut = Specification(project)
            specification = await sut.build()
            jsonschema.validate(specification, schema)
