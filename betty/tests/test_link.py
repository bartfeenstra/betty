from typing import Final

from betty.link import Link, LinkDefinition, StaticLink
from betty.localizables.plain import Plain
from betty.localizer import default_localizer

_dummy_link: Final[Link] = StaticLink("https://example.com", "My First Link")


class TestLinkDefinition:
    def test_link(self) -> None:
        sut = LinkDefinition("my-first-link", link=_dummy_link)
        assert sut.link is _dummy_link

    def test_primary__without_primary(self) -> None:
        sut = LinkDefinition("my-first-link", link=_dummy_link)
        assert not sut.primary

    def test_primary__with_primary(self) -> None:
        sut = LinkDefinition("my-first-link", link=_dummy_link, primary=True)
        assert sut.primary


class TestStaticLink:
    def test_url(self) -> None:
        url = "https://example.com"
        sut = StaticLink(url, "Hello, world!")
        assert sut.url.localize(default_localizer) == url

    def test_label(self) -> None:
        label = Plain("Hello, world!")
        sut = StaticLink("https://example.com", label)
        assert sut.label is label
