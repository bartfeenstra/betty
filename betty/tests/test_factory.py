from collections.abc import Awaitable

from betty.factory import new


class _Value:
    pass


async def test_new__should_not_await_non_coroutine_awaitable() -> None:
    value = _Value()

    async def _new_value() -> _Value:
        return value

    return_value = _new_value()

    def _callback() -> Awaitable[_Value]:
        return return_value

    actual = await new(_callback)
    assert actual is return_value
    assert await actual is value
