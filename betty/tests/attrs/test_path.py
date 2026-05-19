from betty.attrs.path import new_path_attr
from betty.test_utils.locale.localizable import DUMMY_LOCALIZABLE


def test_new_path_attr__minimal() -> None:
    new_path_attr()


def test_new_path_attr__label() -> None:
    attr = new_path_attr(label=DUMMY_LOCALIZABLE)
    assert attr.field.label is DUMMY_LOCALIZABLE


def test_new_path_attr__description() -> None:
    attr = new_path_attr(description=DUMMY_LOCALIZABLE)
    assert attr.field.description is DUMMY_LOCALIZABLE
