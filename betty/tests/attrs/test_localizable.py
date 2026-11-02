from betty.attrs.localizable import new_localizable_attr
from betty.prop import HasProps


class _Owner(HasProps):
    attr = new_localizable_attr(label="-")


def test_new_localizable_attr() -> None:
    owner = _Owner()
    localizable = "Hello, world!"
    owner.attr = localizable
    assert owner.attr == localizable
