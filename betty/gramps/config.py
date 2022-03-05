from typing import Optional, List, Any, Iterable

from reactives import reactive, ReactiveList

from betty.config import Path, ConfigurationError, Configuration, ensure_path
from betty.error import ensure_context
from betty.os import PathLike


class FamilyTreeConfiguration(Configuration):
    def __init__(self, file_path: PathLike):
        super().__init__()
        self.file_path = file_path

    def __eq__(self, other):
        if not isinstance(other, FamilyTreeConfiguration):
            return False
        return self._file_path == other.file_path

    @reactive
    @property
    def file_path(self) -> Path:
        return self._file_path

    @file_path.setter
    def file_path(self, file_path: PathLike) -> None:
        self._file_path = Path(file_path)

    @classmethod
    def load(cls, dumped_configuration: Any) -> Configuration:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError('Family tree configuration must be a mapping (dictionary).')

        if 'file' not in dumped_configuration:
            raise ConfigurationError('Family tree configuration requires a Gramps file to be set.', contexts=['`file`'])

        with ensure_context('`file`'):
            file_path = ensure_path(dumped_configuration['file'])

        return cls(file_path)

    def dump(self) -> Any:
        return {
            'file': str(self.file_path),
        }


class GrampsConfiguration(Configuration):
    def __init__(self, family_trees: Optional[Iterable[FamilyTreeConfiguration]] = None):
        super().__init__()
        self._family_trees = ReactiveList()
        self._family_trees.react(self)
        if family_trees:
            self._family_trees.extend(family_trees)

    @property
    def family_trees(self) -> List[FamilyTreeConfiguration]:
        return self._family_trees

    @classmethod
    def load(cls, dumped_configuration: Any) -> Configuration:
        if not isinstance(dumped_configuration, dict):
            raise ConfigurationError('Gramps configuration must be a mapping (dictionary).')

        if 'family_trees' not in dumped_configuration or not isinstance(dumped_configuration['family_trees'], list):
            raise ConfigurationError('Family trees configuration is required and must must be a list.', contexts=['`family_trees`'])

        loaded_family_tree_configurations = []
        for i, dumped_family_tree_configuration in enumerate(dumped_configuration['family_trees']):
            with ensure_context(f'`{i}`'):
                loaded_family_tree_configurations.append(FamilyTreeConfiguration.load(dumped_family_tree_configuration))

        return cls(loaded_family_tree_configurations)

    def dump(self) -> Any:
        return {
            'family_trees': [
                family_tree.dump()
                for family_tree in self.family_trees
            ]
        }
