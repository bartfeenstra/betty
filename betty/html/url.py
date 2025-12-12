"""
URL handling within HTML.
"""

from collections.abc import Iterable

from lxml.html import fragment_fromstring, tostring

from betty.media_type.media_types import HTML
from betty.url import UrlGenerator


def generate_urls(
    html: str, attribute_names: Iterable[str], *, url_generator: UrlGenerator
) -> str:
    """
    Convert attribute values to URLs.
    """
    generated = False
    fragment = fragment_fromstring(html, create_parent="div")
    attributes_xpath = " or ".join(
        f"boolean(@{attribute_name})" for attribute_name in attribute_names
    )
    for element in fragment.xpath(f"//*[{attributes_xpath}]"):
        for attr_name in element.keys():  # noqa SIM118
            if attr_name in attribute_names:
                attr_value = element.get(attr_name)
                if url_generator.supports(attr_value):
                    element.set(
                        attr_name, url_generator.generate(attr_value, media_type=HTML)
                    )
                    generated = True

    if generated:
        return tostring(fragment).decode("utf-8")[5:-6]
    return html
