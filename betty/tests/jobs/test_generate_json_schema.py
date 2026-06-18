import json

from betty.jobs.generate_json_schema import GenerateJsonSchema
from betty.json_schema import JsonSchemaSchema
from betty.project import Project
from betty.test_utils.job import do


class TestGenerateJsonSchema:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateJsonSchema(project=isolated_project))

        with open(
            isolated_project.www_directory / "schema.json", encoding="utf-8"
        ) as f:
            JsonSchemaSchema().validate(json.loads(f.read()))
