from __future__ import annotations

from inspect import getmembers

from betty.html.attributes import Attributes, AttributesKwargs, _Attribute


class TestAttributes:
    def test_against_descriptors_against_kwargs(self) -> None:
        for attr_name, attr_value in getmembers(Attributes):
            if isinstance(attr_value, _Attribute):
                assert attr_name in AttributesKwargs.__required_keys__

    def test_kwargs_against_descriptors(self) -> None:
        for attr_name in AttributesKwargs.__required_keys__:
            assert isinstance(getattr(Attributes, attr_name), _Attribute)

    def test___str__(self) -> None:
        sut = Attributes()
        assert str(sut) == ""

    def test___html__(self) -> None:
        sut = Attributes()
        assert sut.__html__() == ""

    def test_format__without_values(self) -> None:
        sut = Attributes()
        assert sut.format() == ""

    def test_format__with_values(self) -> None:
        sut = Attributes().set(html_class=["my-first-class"], html_id="my-first-id")
        assert sut.format() == 'class="my-first-class" id="my-first-id"'

    def test_format__with_boolean_attribute(self) -> None:
        sut = Attributes().set(html_checked=True)
        assert sut.format() == "checked"

    def test_format__with_string_attribute(self) -> None:
        sut = Attributes().set(html_id="my-first-id")
        assert sut.format() == 'id="my-first-id"'

    def test_format__with_multiple_string_attribute(self) -> None:
        sut = Attributes().set(html_class=["my-first-class", "my-second-class"])
        assert sut.format() == 'class="my-first-class my-second-class"'

    def test_format__with_boolean_or_string_attribute_with_boolean_value(self) -> None:
        sut = Attributes().set(html_download=True)
        assert sut.format() == "download"

    def test_format__with_boolean_or_string_attribute_with_string_value(self) -> None:
        sut = Attributes().set(html_download="my-first-file")
        assert sut.format() == 'download="my-first-file"'

    def test_set__with_boolean_attribute(self) -> None:
        sut = Attributes()
        sut.set(html_checked=True)
        assert sut.html_checked is True

    def test_set__with_string_attribute(self) -> None:
        sut = Attributes()
        sut.set(html_id="my-first-id")
        assert sut.html_id == "my-first-id"

    def test_set__with_multiple_string_attribute(self) -> None:
        sut = Attributes()
        sut.set(html_class=["my-first-id"])
        assert sut.html_class == ["my-first-id"]

    def test_set__with_boolean_or_string_attribute_with_boolean_value(self) -> None:
        sut = Attributes()
        sut.set(html_download=True)
        assert sut.html_download is True

    def test_set__with_boolean_or_string_attribute_with_string_value(self) -> None:
        sut = Attributes()
        sut.set(html_download="my-first-file")
        assert sut.html_download == "my-first-file"

    def test___set__(self) -> None:
        sut = Attributes()
        sut.html_id = "my-first-id"
        assert sut.html_id == "my-first-id"

    def test_setdefault__with_prior_value(self) -> None:
        sut = Attributes()
        sut.set(html_id="my-prior-id")
        sut.setdefault(html_id="my-default-id")
        assert sut.html_id == "my-prior-id"

    def test_setdefault__without_prior_value(self) -> None:
        sut = Attributes()
        sut.setdefault(html_id="my-default-id")
        assert sut.html_id == "my-default-id"

    def test_set_data(self) -> None:
        sut = Attributes()
        sut.set_data(betty_test="my-first-data-attribute")
        assert sut.format() == 'data-betty-test="my-first-data-attribute"'

    def test_get_data(self) -> None:
        sut = Attributes()
        assert sut.get_data("betty-test") is None
        sut.set_data(betty_test="my-first-data-attribute")
        assert sut.get_data("betty-test") == "my-first-data-attribute"
