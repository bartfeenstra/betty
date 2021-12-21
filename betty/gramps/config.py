from __future__ import annotations

from pathlib import Path
from typing import Optional, Iterable, MutableSequence

from reactives.collections import ReactiveMutableSequence
from reactives.instance.property import reactive_property

from betty.config import Configuration, DumpedConfiguration, VoidableDumpedConfiguration, DumpedConfigurationDict
from betty.config.dump import DumpedConfigurationList, minimize
from betty.config.load import Loader, Field

try:
    from typing_extensions import TypeGuard
except ModuleNotFoundError:
    from typing import TypeGuard  # type: ignore


class FamilyTreeConfiguration(Configuration):
    def __init__(self, file_path: Path | None = None):
        super().__init__()
        self.file_path = file_path

    def __eq__(self, other):
        if not isinstance(other, FamilyTreeConfiguration):
            return False
        return self._file_path == other.file_path

    @property
    @reactive_property
    def file_path(self) -> Path | None:
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: Path | None) -> None:
        self._file_path = file_path

    def load(self, dumped_configuration: DumpedConfiguration, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'file': Field(
                True,
                loader.assert_path,  # type: ignore
                lambda x: loader.assert_setattr(self, 'file_path', x)
            )
        })

    def dump(self) -> VoidableDumpedConfiguration:
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

    def load(self, dumped_configuration: DumpedConfiguration, loader: Loader) -> None:
        loader.assert_record(dumped_configuration, {
            'family_trees': Field(
                True,
                self._load_family_trees,  # type: ignore
            ),
        })

    def _load_family_trees(self, dumped_configuration, loader: Loader) -> TypeGuard[DumpedConfigurationList[DumpedConfiguration]]:
        loader.on_commit(self._family_trees.clear)
        return loader.assert_sequence(
            dumped_configuration,
            self._load_family_tree,  # type: ignore
        )

    def _load_family_tree(self, dumped_configuration: DumpedConfiguration, loader: Loader) -> TypeGuard[DumpedConfigurationDict[DumpedConfiguration]]:
        with loader.context() as errors:
            family_tree_configuration = FamilyTreeConfiguration()
            family_tree_configuration.load(dumped_configuration, loader)
            loader.on_commit(lambda: self._family_trees.append(family_tree_configuration))
        return errors.valid

    def dump(self) -> VoidableDumpedConfiguration:
        return {
            'family_trees': [
                minimize(family_tree.dump(), False)
                for family_tree in self.family_trees
            ]
        }
