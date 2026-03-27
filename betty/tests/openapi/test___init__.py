import pytest

from betty.openapi import Specification
from betty.openapi.schema import SpecificationSchema
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
        SpecificationSchema().validate(specification)
