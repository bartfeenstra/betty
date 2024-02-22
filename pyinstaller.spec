# -*- mode: python ; coding: utf-8 -*-

from betty._package.pyinstaller import a_pyz_exe_coll
from betty.asyncio import wait


a, pyz, exe, coll = wait(a_pyz_exe_coll())
