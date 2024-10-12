from typing import Sequence

from typing_extensions import override

from betty.copyright_notice import CopyrightNotice
from betty.project.extension.demo.copyright_notice import Streetmix
from betty.test_utils.copyright_notice import CopyrightNoticeTestBase


class TestStreetmix(CopyrightNoticeTestBase):
    @override
    def get_sut_class(self) -> type[CopyrightNotice]:
        return Streetmix

    @override
    def get_sut_instances(self) -> Sequence[CopyrightNotice]:
        return [Streetmix()]
