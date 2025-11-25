import pytest
from typing_extensions import override

from betty.copyright_notice import CopyrightNotice
from betty.plugin import PluginDefinition
from betty.project.extension.demo.copyright_notice import Streetmix
from betty.test_utils.copyright_notice import (
    CopyrightNoticePluginTestBase,
    CopyrightNoticeTestBase,
)


class TestStreetmixDefinition(CopyrightNoticePluginTestBase):
    @override
    @pytest.fixture
    def sut(self) -> PluginDefinition:
        return Streetmix.plugin


class TestStreetmix(CopyrightNoticeTestBase):
    @override
    @pytest.fixture
    def sut(self) -> CopyrightNotice:
        return Streetmix()
