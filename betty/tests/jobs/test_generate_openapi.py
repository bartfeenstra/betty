import json

from betty.jobs.generate_openapi import GenerateOpenapi
from betty.openapi.schema import SpecificationSchema
from betty.project import Project
from betty.test_utils.job import do


class TestGenerateOpenapi:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateOpenapi(project=isolated_project))

        with open(
            isolated_project.www_directory / "api" / "index.json", encoding="utf-8"
        ) as f:
            SpecificationSchema().validate(json.loads(f.read()))
