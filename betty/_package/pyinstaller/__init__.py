import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from PyInstaller.building.api import PYZ, EXE
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_submodules as pyinstaller_collect_submodules

from betty._package import get_data_paths
from betty._package.pyinstaller.hooks import HOOKS_DIRECTORY_PATH
from betty.app import App, AppExtensionConfiguration, Configuration
from betty.asyncio import sync
from betty.fs import ROOT_DIRECTORY_PATH
from betty.http_api_doc import HttpApiDoc
from betty.maps import Maps
from betty.npm import _Npm, build_assets
from betty.trees import Trees


def _collect_submodules() -> List[str]:
    return [submodule for submodule in pyinstaller_collect_submodules('betty') if _filter_submodule(submodule)]


def _filter_submodule(submodule: str) -> bool:
    if submodule.startswith('betty.tests'):
        return False
    if submodule.startswith('betty._package'):
        return False
    return True


async def _build_assets() -> None:
    npm_builder_extension_types = {HttpApiDoc, Maps, Trees}
    with TemporaryDirectory() as output_directory_path:
        configuration = Configuration(output_directory_path, 'https://example.com')
        configuration.extensions.add(AppExtensionConfiguration(_Npm))
        for extension_type in npm_builder_extension_types:
            configuration.extensions.add(AppExtensionConfiguration(extension_type))
        async with App(configuration) as app:
            await asyncio.gather(*[
                build_assets(app.extensions[extension_type])
                for extension_type
                in npm_builder_extension_types
            ])


@sync
async def a_pyz_exe():
    await _build_assets()
    root = Path(__file__).parents[3]
    block_cipher = None
    datas = [
        (file_path, str(file_path.parent.relative_to(root)))
        for file_path
        in get_data_paths()
    ]
    hiddenimports = [
        *_collect_submodules(),
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
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              [],
              name='betty',
              debug=False,
              bootloader_ignore_signals=False,
              strip=False,
              upx=True,
              upx_exclude=[],
              runtime_tmpdir=None,
              console=False,
              icon=str(ROOT_DIRECTORY_PATH / 'betty' / 'assets' / 'public' / 'static' / 'betty.ico'))
    return a, pyz, exe
