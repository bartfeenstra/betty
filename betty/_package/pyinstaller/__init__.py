"""Integrate Betty with PyInstaller."""

import sys

from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis
from setuptools import find_packages

from betty._package import prebuild
from betty._package.pyinstaller.hooks import HOOKS_DIRECTORY_PATH
from betty.fs import ROOT_DIRECTORY_PATH


async def a_pyz_exe_coll() -> tuple[Analysis, PYZ, EXE, COLLECT]:
    """
    Build PyInstaller's spec components.
    """
    if sys.platform == "linux":
        exe_name = "betty"
    elif sys.platform == "darwin":
        exe_name = "betty.app"
    elif sys.platform == "win32":
        exe_name = "betty.exe"
    else:
        raise RuntimeError(f"Unsupported platform {sys.platform}.")

    await prebuild()
    block_cipher = None
    datas = []
    data_file_path_patterns = [
        # Assets.
        "betty/assets/**",
        "betty/extension/*/assets/**",
        # Webpack.
        ".browserslistrc",
        "betty/extension/*/webpack/**",
        "tsconfig.json",
        "prebuild/**",
    ]
    for data_file_path_pattern in data_file_path_patterns:
        for data_file_path in ROOT_DIRECTORY_PATH.glob(data_file_path_pattern):
            if data_file_path.is_file():
                datas.append(
                    (
                        str(data_file_path),
                        str(data_file_path.parent.relative_to(ROOT_DIRECTORY_PATH)),
                    )
                )
    hiddenimports = [
        *find_packages(
            ".",
            exclude=[
                "betty.tests",
                "betty.tests.*",
            ],
        ),
        "babel.numbers",
    ]
    a = Analysis(
        ["betty/_package/pyinstaller/main.py"],
        pathex=["./"],
        binaries=[],
        datas=datas,
        hiddenimports=hiddenimports,
        hookspath=[str(HOOKS_DIRECTORY_PATH)],
        runtime_hooks=[],
        excludes=[],
        win_no_prefer_redirects=False,
        win_private_assemblies=False,
        cipher=block_cipher,
        noarchive=False,
    )
    pyz = PYZ(
        a.pure,
        a.zipped_data,
        cipher=block_cipher,
    )
    exe = EXE(
        pyz,
        a.binaries,
        a.scripts,
        [],
        name=exe_name,
        exclude_binaries=True,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        console=False,
        icon=str(
            ROOT_DIRECTORY_PATH / "betty" / "assets" / "public" / "static" / "betty.ico"
        ),
    )
    coll = COLLECT(
        exe,
        a.datas,
        a.zipfiles,
        name="betty",
    )
    return a, pyz, exe, coll
