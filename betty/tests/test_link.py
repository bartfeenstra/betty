from betty.html import NavigationLink
from betty.link import LinkDefinition

_DUMMY_LINK = NavigationLink("https://example.com", "My First Link")


class TestLinkDefinition:
    def test_link(self) -> None:
        sut = LinkDefinition("my-first-link", link=_DUMMY_LINK)
        assert sut.link is _DUMMY_LINK

    def test_primary__without_primary(self) -> None:
        sut = LinkDefinition("my-first-link", link=_DUMMY_LINK)
        assert not sut.primary

    def test_primary__with_primary(self) -> None:
        sut = LinkDefinition("my-first-link", link=_DUMMY_LINK, primary=True)
        assert sut.primary
