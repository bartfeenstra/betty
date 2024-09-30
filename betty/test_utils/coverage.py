"""
Utilities for asserting test coverage.
"""

from __future__ import annotations

import pkgutil
from abc import abstractmethod, ABC
from configparser import ConfigParser
from contextlib import suppress
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import TypeVar, Generic, Union, TYPE_CHECKING, Iterator, TypeAlias, override


from betty.fs import ROOT_DIRECTORY_PATH
from betty.importlib import import_any
from betty.string import snake_case_to_upper_camel_case

if TYPE_CHECKING:
    from collections.abc import (
        Sequence,
    )
    from typing import Any


Errors: TypeAlias = Iterator[tuple[Path, str]]


class MissingReason(Enum):
    """
    Reasons why test coverage is missing.
    """

    ABSTRACT = "This testable is abstract"
    COVERAGERC = "This testable is excluded by .coveragerc"
    INTERNAL = "This testable is internal to Betty itself"
    PRIVATE = "This testable is private"
    SHOULD_BE_COVERED = "This testable should be covered by a test but isn't yet"


@lru_cache
def get_coveragerc_ignore_modules() -> Sequence[Path]:
    """
    Get modules that are ignored by .coveragerc.
    """
    coveragerc = ConfigParser()
    coveragerc.read(ROOT_DIRECTORY_PATH / ".coveragerc")
    omit = coveragerc.get("run", "omit").strip().split("\n")
    modules = []
    for omit_pattern in omit:
        for module_path in Path().glob(omit_pattern):
            if module_path.suffix != ".py":
                continue
            if not module_path.is_file():
                continue
            modules.append(module_path.resolve())
    return modules


def _name_to_path(fully_qualified_type_name: str) -> Path:
    module_name = (
        fully_qualified_type_name.rsplit(":", 1)[0]
        if ":" in fully_qualified_type_name
        else fully_qualified_type_name
    )
    return Path(import_any(module_name).__file__)


_ParentT = TypeVar("_ParentT", bound="_Testable[Any] | None")
_ChildT = TypeVar("_ChildT", bound="_Testable[Any]")


class _Testable(ABC, Generic[_ParentT]):
    _parent: _ParentT

    def __init__(self, name: str, *, missing: MissingReason | None = None):
        self._name = name
        self._missing = self.auto_ignore
        if missing:
            assert not self.missing, f"{self} is already ignored ({self.missing.value})"
            self._missing = missing

    @property
    def missing(self) -> MissingReason | None:
        return self._missing

    @property
    def parent(self) -> _ParentT:
        return self._parent

    @parent.setter
    def parent(self, parent: _ParentT) -> None:
        self._parent = parent

    @property
    def auto_ignore(self) -> MissingReason | None:
        if self.testable_name.startswith("_"):
            return MissingReason.PRIVATE
        return None

    @property
    def testable_name(self) -> str:
        return self._name

    @property
    def testable_file_path(self) -> Path:
        return _name_to_path(self.testable_name)

    @property
    def testable_exists(self) -> bool:
        return self._exists(self.testable_name)

    @property
    @abstractmethod
    def test_name(self) -> str:
        pass

    def test_exists(self) -> bool:
        return self._exists(self.test_name)

    def _exists(self, name: str) -> bool:
        try:
            import_any(name)
            return True
        except ImportError:
            return False

    def validate(self) -> Errors:
        if not self.testable_exists:
            yield self.testable_file_path, f"{self.testable_name} does not exist"
            return

        if self.missing and self.test_exists():
            yield (
                self.testable_file_path,
                f"{self.testable_name} was marked lacking a test, but {self.test_name} unexpectedly exists",
            )
        if not self.missing and not self.test_exists():
            yield (
                self.testable_file_path,
                f"{self.testable_name} unexpectedly lacks a matching test {self.test_name}",
            )


class _HasChildren(_Testable[_ParentT], Generic[_ParentT, _ChildT]):
    def __init__(
        self,
        name: str,
        *,
        missing: MissingReason | None = None,
        children: set[_ChildT] | None = None,
    ):
        super().__init__(name, missing=missing)
        self._children = children or set()
        self._auto_children()
        for child in self.children:
            child.parent = self

    def _auto_children(self) -> None:
        pass

    @property
    def children(self) -> set[_ChildT]:
        return self._children

    @override
    def validate(self) -> Errors:
        yield from super().validate()
        for child in self.children:
            yield from child.validate()


class Module(_HasChildren[Union["Module", None], Union["Module", "Class", "Function"]]):
    """
    A testable module.
    """

    @override
    def _auto_children(self) -> None:
        # @todo Also add ignores from get_coveragerc_ignore_modules()
        # @todo, No, do that in the Betty-specific concrete test!
        if self.testable_file_path.name == "__init__.py":
            child_testable_names = {
                child.testable_name
                for child in self.children
                if isinstance(child, Module)
            }
            for module_info in pkgutil.iter_modules(
                [str(self.testable_file_path.parent)]
            ):
                module_testable_name = f"{self.testable_name}.{module_info.name}"
                if (
                    module_testable_name not in child_testable_names
                    and _name_to_path(module_testable_name)
                    not in get_coveragerc_ignore_modules()
                ):
                    self._children = {
                        *self._children,
                        Module(module_testable_name),
                    }

    @property
    def testable_module_name(self) -> str:
        """
        The testable's module name.
        """
        return self.testable_name.split(".")[-1]

    @override
    @property
    def test_name(self) -> str:
        if self.testable_file_path.name == "__init__.py":
            return f"betty.tests.{self.testable_name[6:]}.test___init__"
        else:
            return f"betty.tests.{self.testable_name[6:-len(self.testable_module_name)]}test_{self.testable_module_name}"

    def _prefix(self):
        pass


class InternalModule(Module):
    """
    A module that is internal and does not need test coverage.
    """

    def __init__(self, name: str):
        super().__init__(name, missing=MissingReason.INTERNAL)

    @override
    def _auto_children(self) -> None:
        return None


class Function(_Testable[Module]):
    """
    A testable module function.
    """

    @override
    @property
    def test_name(self) -> str:
        _, testable_function_name = self.testable_name.split(":")
        test_module_name = f"betty.tests.{self.testable_name[6:]}"
        test_class_name = (
            f"Test{snake_case_to_upper_camel_case(testable_function_name)}"
        )
        return f"{test_module_name}:{test_class_name}"


class Method(_Testable["Class"]):
    """
    A testable method.
    """

    @override
    @property
    def auto_ignore(self) -> MissingReason | None:
        missing = super().auto_ignore
        if missing is not None:
            return missing
        with suppress(ImportError):
            if getattr(import_any(self.testable_name), "__isabstractmethod__", False):
                return MissingReason.ABSTRACT
        return None

    @override
    @property
    def test_name(self) -> str:
        _, testable_attrs = self.testable_name.split(":")
        test_module_name = f"betty.tests.{self.testable_name[6:]}"
        testable_class_name, testable_method_name = testable_attrs.split(".")
        test_class_name = f"Test{testable_class_name}"
        test_method_name = f"test_{testable_method_name}"
        return f"{test_module_name}:{test_class_name}.{test_method_name}"


class Class(_HasChildren[Module, Method]):
    """
    A testable class.
    """

    @override
    @property
    def test_name(self) -> str:
        testable_module_name, testable_class_name = self.testable_name.split(":")
        test_module_name = f"betty.tests.{testable_module_name[6:]}"
        test_class_name = f"Test{testable_class_name}"
        return f"{test_module_name}:{test_class_name}"
