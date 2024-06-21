# -*- mode: python ; coding: utf-8 -*-

from betty._package.pyinstaller import a_pyz_exe_coll
from betty.asyncio import wait_to_thread


a, pyz, exe, coll = wait_to_thread(a_pyz_exe_coll())
