import logging
from typing import override

import pytest

from betty.test_utils.user.ui import StaticUi
from betty.user.logging import UiHandler, log_level_to_severity


def test_log_level_to_severity() -> None:
    for log_level in range(99):
        assert log_level_to_severity(log_level)


class _TestUserHandlerLogger(logging.Logger):
    @override
    def isEnabledFor(self, level: int) -> bool:
        return True


class TestUiHandler:
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
        ui = StaticUi()
        message = "Hello, world!"
        sut = UiHandler(ui)
        logger.addHandler(sut)
        async with sut:
            logger.log(log_level, message)
        ui.assert_log(message)
