import pytest
from typing_extensions import override

from betty.copyright_notice import CopyrightNotice
from betty.copyright_notice.copyright_notices import ProjectAuthor, PublicDomain
from betty.locale.localizable import Plain
from betty.plugin import PluginDefinition
from betty.test_utils.copyright_notice import (
    CopyrightNoticeDefinitionTestBase,
    CopyrightNoticeTestBase,
)


class TestProjectAuthorDefinition(CopyrightNoticeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return ProjectAuthor.plugin


class TestProjectAuthor(CopyrightNoticeTestBase):
    @override
    @pytest.fixture(
        params=[
            None,
            Plain("My First Author"),
        ]
    )
    def sut(self, request: pytest.FixtureRequest) -> CopyrightNotice:
        return ProjectAuthor(request.param)


class TestPublicDomainDefinition(CopyrightNoticeDefinitionTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return PublicDomain.plugin


class TestPublicDomain(CopyrightNoticeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> CopyrightNotice:
        return PublicDomain()
