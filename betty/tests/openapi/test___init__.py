import pytest

from betty.json_schema.validate import validate
from betty.openapi import OPENAPI_SPECIFICATION_SCHEMA, Specification
from betty.test_utils.conftest import IsolatedProjectFactory


class TestSpecification:
    @pytest.mark.parametrize(
        "clean_urls",
        [
            True,
            False,
        ],
    )
    async def test_build(
        self, clean_urls: bool, isolated_project_factory: IsolatedProjectFactory
    ) -> None:
        async with isolated_project_factory(clean_urls=clean_urls) as project:
            sut = Specification(project)
            specification = await sut.build()
        validate(OPENAPI_SPECIFICATION_SCHEMA, specification)
