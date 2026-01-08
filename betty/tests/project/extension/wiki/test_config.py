from betty.project.extension.wiki.config import WikiConfiguration
from betty.test_utils.data import HasDataTestBase


class TestWikiConfiguration(HasDataTestBase[WikiConfiguration]):
    sut_cls = WikiConfiguration
