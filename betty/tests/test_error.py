from betty.error import do_raise


def test_do_raise() -> None:
    expected = RuntimeError()
    try:
        do_raise(expected)
    except BaseException as actual:
        assert actual is expected  # noqa: PT017
