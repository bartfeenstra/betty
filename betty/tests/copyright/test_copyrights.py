from typing import Sequence

from typing_extensions import override

from betty.copyright import Copyright
from betty.copyright.copyrights import ProjectAuthor
from betty.locale.localizable import plain
from betty.test_utils.copyright import CopyrightTestBase


class TestProjectAuthor(CopyrightTestBase):
    @override
    def get_sut_class(self) -> type[Copyright]:
        return ProjectAuthor

    @override
    def get_sut_instances(self) -> Sequence[Copyright]:
        return [ProjectAuthor(None), ProjectAuthor(plain("My First Author"))]
