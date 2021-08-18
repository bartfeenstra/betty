from pathlib import Path
from typing import List

from PyInstaller.building.api import PYZ, EXE
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_submodules as pyinstaller_collect_submodules

from betty._package import get_data_paths
from betty.fs import ROOT_DIRECTORY_PATH


def collect_submodules() -> List[str]:
    return [submodule for submodule in pyinstaller_collect_submodules('betty') if _filter_submodule(submodule)]


def _filter_submodule(submodule: str) -> bool:
    if submodule.startswith('betty.tests'):
        return False
    if submodule.startswith('betty._package'):
        return False
    return True


def a_pyz_exe():
    root = Path(__file__).parents[3]
    block_cipher = None
    datas = [
        (file_path, str(file_path.parent.relative_to(root))) for file_path in get_data_paths()
    ]
    hiddenimports = [
        *collect_submodules(),
        'babel.numbers'
    ]
    a = Analysis(['betty/_package/pyinstaller/main.py'],
                 pathex=['./'],
                 binaries=[],
                 datas=datas,
                 hiddenimports=hiddenimports,
                 hookspath=[],
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
