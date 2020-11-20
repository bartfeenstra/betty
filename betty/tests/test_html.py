from betty.asyncio import sync
from betty.html import HtmlProvider
from betty.tests import TestCase


class HtmlProviderTest(TestCase):
    class _HtmlProviderDummy(HtmlProvider):
        pass

    @sync
    async def test_public_css_paths(self):
        sut = self._HtmlProviderDummy()
        self.assertEquals(0, len(sut.public_css_paths))

    @sync
    async def test_public_js_paths(self):
        sut = self._HtmlProviderDummy()
        self.assertEquals(0, len(sut.public_js_paths))
