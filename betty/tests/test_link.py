from betty.link import LinkDefinition, StaticLink
from betty.locale.localizable.plain import Plain
from betty.locale.localize import DEFAULT_LOCALIZER

_DUMMY_LINK = StaticLink("https://example.com", "My First Link")


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


class TestStaticLink:
    def test_url(self) -> None:
        url = "https://example.com"
        sut = StaticLink(url, "Hello, world!")
        assert sut.url.localize(DEFAULT_LOCALIZER) == url

    def test_label(self) -> None:
        label = Plain("Hello, world!")
        sut = StaticLink("https://example.com", label)
        assert sut.label is label
