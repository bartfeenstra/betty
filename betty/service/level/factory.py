"""
Service level factories.
"""

from typing import TypeAlias, TypeVar

from betty.app.factory import AppFactory
from betty.factory import Factory
from betty.project.factory import ProjectFactory, ProjectTarget

_T = TypeVar("_T")


AnyFactoryTarget: TypeAlias = ProjectTarget[_T]
"""
A factory target for any service level.
"""


AnyFactory: TypeAlias = Factory | AppFactory | ProjectFactory
"""
A factory for any service level.
"""
