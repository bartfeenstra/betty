from betty.attrs.path import new_path_attr


def test_new_path_attr__minimal() -> None:
    new_path_attr()


def test_new_path_attr__label() -> None:
    label = "Hello, world!"
    attr = new_path_attr(label=label)
    assert attr.field.label is label


def test_new_path_attr__description() -> None:
    description = "Hello, world!"
    attr = new_path_attr(description=description)
    assert attr.field.description is description
