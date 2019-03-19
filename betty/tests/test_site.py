from unittest import TestCase
from unittest.mock import Mock

from betty.ancestry import Ancestry
from betty.config import Configuration
from betty.site import Site


class SiteTest(TestCase):
    def test_ancestry_should_return(self):
        ancestry = Ancestry()
        configuration = Mock(Configuration)
        sut = Site(ancestry, configuration)
        self.assertEquals(sut.ancestry, ancestry)

    def test_configuration_should_return(self):
        ancestry = Ancestry()
        configuration = Mock(Configuration)
        sut = Site(ancestry, configuration)
        self.assertEquals(sut.configuration, configuration)
