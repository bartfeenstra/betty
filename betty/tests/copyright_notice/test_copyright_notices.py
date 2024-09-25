from typing import Sequence

from typing_extensions import override

from betty.copyright_notice import CopyrightNotice
from betty.copyright_notice.copyright_notices import ProjectAuthor, PublicDomain
from betty.locale.localizable import plain
from betty.test_utils.copyright_notice import CopyrightNoticeTestBase


class TestProjectAuthor(CopyrightNoticeTestBase):
    @override
    def get_sut_class(self) -> type[CopyrightNotice]:
        return ProjectAuthor

    @override
    def get_sut_instances(self) -> Sequence[CopyrightNotice]:
        return [
            ProjectAuthor(None),
            ProjectAuthor(plain("My First Author")),
        ]


class TestPublicDomain(CopyrightNoticeTestBase):
    @override
    def get_sut_class(self) -> type[CopyrightNotice]:
        return PublicDomain

    @override
    def get_sut_instances(self) -> Sequence[CopyrightNotice]:
        return [
            PublicDomain(),
        ]
