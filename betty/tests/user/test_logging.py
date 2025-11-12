import logging

import pytest
from typing_extensions import override

from betty.test_utils.user import StaticUser
from betty.user.logging import UserHandler


class _TestUserHandlerLogger(logging.Logger):
    @override
    def isEnabledFor(self, level: int) -> bool:
        return True


class TestUserHandler:
    @pytest.mark.parametrize(
        ("log_level", "message_type"),
        [
            (logging.ERROR, "error"),
            (logging.WARNING, "warning"),
            (logging.INFO, "information"),
            (logging.DEBUG, "debug"),
            (logging.NOTSET, "debug"),
        ],
    )
    async def test_emit(self, log_level: int, message_type: str) -> None:
        logger = _TestUserHandlerLogger(self.__class__.__name__)
        logging.disable()
        logger.setLevel(logging.NOTSET)
        user = StaticUser()
        message = "Hello, world!"
        sut = UserHandler(user)
        logger.addHandler(sut)
        await sut.start()
        try:
            logger.log(log_level, message)
        finally:
            await sut.stop()
        user.assert_message_log(message)
