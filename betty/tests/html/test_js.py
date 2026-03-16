from betty.html.js import JsResourceDefinition


class TestJsResourceDefinition:
    def test_resource(self) -> None:
        resource = object()
        sut = JsResourceDefinition("my-first-resource", resource=resource)
        assert sut.resource is resource
