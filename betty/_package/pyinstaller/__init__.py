"""Integrate Betty with PyInstaller."""
import sys
from glob import glob
from pathlib import Path

from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis
from setuptools import find_packages

from betty._package.pyinstaller.hooks import HOOKS_DIRECTORY_PATH
from betty.app import App
from betty.app.extension import discover_extension_types, Extension
from betty.asyncio import gather
from betty.extension.npm import _Npm, build_assets, NpmBuilder
from betty.fs import ROOT_DIRECTORY_PATH
from betty.project import ExtensionConfiguration


async def _build_assets() -> None:
    npm_builder_extension_types: list[type[NpmBuilder & Extension]] = [
        extension_type
        for extension_type
        in discover_extension_types()
        if issubclass(extension_type, NpmBuilder)
    ]
    async with App() as app:
        app.project.configuration.extensions.append(ExtensionConfiguration(_Npm))
        for extension_type in npm_builder_extension_types:
            app.project.configuration.extensions.append(ExtensionConfiguration(extension_type))
        await gather(*([
            build_assets(app.extensions[extension_type])  # type: ignore[arg-type]
            for extension_type
            in npm_builder_extension_types
        ]))


async def a_pyz_exe_coll() -> tuple[Analysis, PYZ, EXE, COLLECT]:
    """
    Build PyInstaller's spec components.
    """
    if sys.platform == 'linux':
        exe_name = 'betty'
    elif sys.platform == 'darwin':
        exe_name = 'betty.app'
    elif sys.platform == 'win32':
        exe_name = 'betty.exe'
    else:
        raise RuntimeError(f'Unsupported platform {sys.platform}.')

    await _build_assets()
    block_cipher = None
    datas = []
    data_file_path_patterns = [
        'betty/assets/**',
        'betty/extension/*/assets/**',
    ]
    for data_file_path_pattern in data_file_path_patterns:
        for data_file_path_str in glob(data_file_path_pattern, recursive=True, root_dir=ROOT_DIRECTORY_PATH):
            data_file_path = Path(data_file_path_str)
            if data_file_path.is_file():
                datas.append((data_file_path_str, str(data_file_path.parent)))
    hiddenimports = [
        *find_packages(
            '.',
            exclude=[
                'betty.tests',
                'betty.tests.*',
            ],
        ),
        'babel.numbers'
    ]
    a = Analysis(
        ['betty/_package/pyinstaller/main.py'],
        pathex=['./'],
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
        icon=str(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'public' / 'static' / 'betty.ico'),
    )
    coll = COLLECT(
        exe,
        a.datas,
        a.zipfiles,
        name='betty',
    )
    return a, pyz, exe, coll
