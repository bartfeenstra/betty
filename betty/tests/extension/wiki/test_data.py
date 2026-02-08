from betty.extension.wiki.data import WikiConfiguration
from betty.test_utils.data import DataTestBase


class TestWikiConfiguration(DataTestBase[WikiConfiguration]):
    sut_cls = WikiConfiguration
