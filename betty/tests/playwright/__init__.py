from os import environ

import pytest

check_skip = pytest.mark.skipif(
    environ.get("BETTY_TEST_SKIP_PLAYWRIGHT", False) is not False,
    reason="Playwright tests are being skipped",
)
