from pathlib import Path
from typing import Optional, Iterable, MutableSequence

from reactives.collections import ReactiveMutableSequence
from reactives.instance.property import reactive_property

from betty.config import Configuration, DumpedConfigurationImport, DumpedConfigurationExport, DumpedConfigurationDict
from betty.config.dump import DumpedConfigurationList
from betty.config.load import Loader, Field
from betty.os import PathLike

try:
    from typing_extensions import TypeGuard
except ModuleNotFoundError:
    from typing import TypeGuard  # type: ignore


class FamilyTreeConfiguration(Configuration):
    def __init__(self, file_path: Optional[PathLike] = None):
        super().__init__()
        self.file_path = file_path  # type: ignore[assignment]

    def __eq__(self, other):
        if not isinstance(other, FamilyTreeConfiguration):
            return False
        return self._file_path == other.file_path

    @property
    @reactive_property
    def file_path(self) -> Optional[Path]:
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: Optional[PathLike]) -> None:
        self._file_path = Path(file_path) if file_path else None

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'file': Field(
                True,
                loader.assert_path,  # type: ignore
                lambda x: loader.assert_setattr(self, 'file_path', x)
            )
        })

    def dump(self) -> DumpedConfigurationExport:
        return {
            'file': str(self.file_path),
        }


class GrampsConfiguration(Configuration):
    def __init__(self, family_trees: Optional[Iterable[FamilyTreeConfiguration]] = None):
        super().__init__()
        self._family_trees = ReactiveMutableSequence[FamilyTreeConfiguration]()
        self._family_trees.react(self)
        if family_trees:
            self._family_trees.extend(family_trees)

    @property
    def family_trees(self) -> MutableSequence[FamilyTreeConfiguration]:
        return self._family_trees

    def load(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'family_trees': Field(
                True,
                self._load_family_trees,  # type: ignore
            ),
        })

    def _load_family_trees(self, dumped_configuration, loader: Loader) -> TypeGuard[DumpedConfigurationList[DumpedConfigurationImport]]:
        loader.on_commit(self._family_trees.clear)
        return loader.assert_sequence(
            dumped_configuration,
            self._load_family_tree,  # type: ignore
        )

    def _load_family_tree(self, dumped_configuration: DumpedConfigurationImport, loader: Loader) -> TypeGuard[DumpedConfigurationDict[DumpedConfigurationImport]]:
        with loader.context() as errors:
            family_tree_configuration = FamilyTreeConfiguration()
            family_tree_configuration.load(dumped_configuration, loader)
            loader.on_commit(lambda: self._family_trees.append(family_tree_configuration))
        return errors.valid

    def dump(self) -> DumpedConfigurationExport:
        return {
            'family_trees': [
                family_tree.dump()
                for family_tree in self.family_trees
            ]
        }
