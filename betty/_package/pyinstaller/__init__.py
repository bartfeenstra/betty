import asyncio
import inspect
import sys
from importlib import import_module
from pathlib import Path

from PyInstaller.building.api import PYZ, EXE
from PyInstaller.building.build_main import Analysis

from betty._package import get_data_paths, find_packages
from betty._package.pyinstaller.hooks import HOOKS_DIRECTORY_PATH
from betty.app import App
from betty.asyncio import sync, wait
from betty.fs import ROOT_DIRECTORY_PATH
from betty.extension import HttpApiDoc, Maps, Trees
from betty.extension.npm import _Npm, build_assets
from betty.project import ExtensionConfiguration


async def _build_assets() -> None:
    npm_builder_extension_types = {HttpApiDoc, Maps, Trees}
    async with App() as app:
        app.project.configuration.extensions.append(ExtensionConfiguration(_Npm))
        for extension_type in npm_builder_extension_types:
            app.project.configuration.extensions.append(ExtensionConfiguration(extension_type))
        await asyncio.gather(*[
            build_assets(app.extensions[extension_type])
            for extension_type
            in npm_builder_extension_types
        ])


@sync
async def a_pyz_exe() -> tuple[Analysis, PYZ, EXE]:
    await _build_assets()
    root = Path(__file__).parents[3]
    block_cipher = None
    datas = []
    for module_name, file_paths in wait(get_data_paths()).items():
        for file_path in file_paths:
            data_file_path = (Path(inspect.getfile(import_module(module_name))).parent / file_path).relative_to(root)
            datas.append((str(data_file_path), str(data_file_path.parent)))
    hiddenimports = [
        *find_packages(),
        'babel.numbers'
    ]
    a = Analysis(['betty/_package/pyinstaller/main.py'],
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
                 noarchive=False)
    pyz = PYZ(a.pure, a.zipped_data,
              cipher=block_cipher)
    if sys.platform == 'linux':
        exe_name = 'betty'
    elif sys.platform == 'darwin':
        exe_name = 'betty.app'
    elif sys.platform == 'win32':
        exe_name = 'betty.exe'
    else:
        raise RuntimeError(f'Unsupported platform {sys.platform}.')
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              name=exe_name,
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              upx_exclude=[],
              runtime_tmpdir=None,
              console=False,
              icon=str(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'public' / 'static' / 'betty.ico'))
    return a, pyz, exe
