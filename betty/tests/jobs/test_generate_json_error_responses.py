from betty.jobs.generate_json_error_responses import GenerateJsonErrorResponses
from betty.project import Project
from betty.test_utils.jinja import assert_betty_json
from betty.test_utils.job import do


class TestGenerateJsonErrorResponses:
    async def test_do(self, isolated_project: Project) -> None:
        await do(GenerateJsonErrorResponses(project=isolated_project))

        for code in [401, 403, 404]:
            await assert_betty_json(
                isolated_project, f".error/{code}.json", "errorResponse"
            )
