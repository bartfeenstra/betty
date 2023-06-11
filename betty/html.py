class CssProvider:
    @property
    def public_css_paths(self) -> list[str]:
        raise NotImplementedError(repr(self))


class JsProvider:
    @property
    def public_js_paths(self) -> list[str]:
        raise NotImplementedError(repr(self))
