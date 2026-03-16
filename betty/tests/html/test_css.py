from betty.html.css import CssResourceDefinition


class TestCssResourceDefinition:
    def test_resource(self) -> None:
        resource = object()
        sut = CssResourceDefinition("my-first-resource", resource=resource)
        assert sut.resource is resource
