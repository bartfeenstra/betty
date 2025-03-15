from pathlib import Path

import aiofiles
import pytest
from playwright.async_api import Page

from betty.fs import ROOT_DIRECTORY_PATH
from betty.locale.localizer import DEFAULT_LOCALIZER
from betty.serve import BuiltinServer
from betty.subprocess import run_process


async def tsc(file_path: Path, output_directory_path: Path) -> None:
    await run_process(
        [
            "npx",
            "tsc",
            "--module",
            "esnext",
            "--target",
            "es2017",
            "--moduleResolution",
            "bundler",
            "--outDir",
            str(output_directory_path),
            str(file_path),
        ],
        ROOT_DIRECTORY_PATH,
    )


@pytest.mark.asyncio(loop_scope="session")
async def test(page: Page, tmp_path: Path) -> None:
    await tsc(ROOT_DIRECTORY_PATH / "js" / "index.ts", tmp_path)
    await tsc(ROOT_DIRECTORY_PATH / "js" / "main.ts", tmp_path)
    async with aiofiles.open(tmp_path / "index.html", "w") as f:
        await f.write("""
<!doctype html>
<html>
<head>
    <title>test</title>
</head>
<body>
<script type="module">
'use strict'

import {BETTY as BETTY_ONE} from "/main.js"
import {BETTY as BETTY_TWO} from "/main.js"
document.BETTY_ONE = BETTY_ONE
document.BETTY_TWO = BETTY_TWO
</script>
</body>
</html>

        """)
    async with BuiltinServer(tmp_path, localizer=DEFAULT_LOCALIZER) as server:
        await page.goto(server.public_url)
        assert await page.evaluate("() => document.BETTY_ON")
        assert await page.evaluate("() => document.BETTY_ONE && document.BETTY_ONE === document.BETTY_TWO")
