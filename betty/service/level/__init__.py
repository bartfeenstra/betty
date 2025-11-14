"""
Service levels.
"""

from typing import TypeAlias, TypeVar

from betty.app import App
from betty.project import Project

_T = TypeVar("_T")

ServiceLevel: TypeAlias = None | App | Project
"""
A service level.

A runtime Betty application consists of three types of service containers:

- :py:class:`betty.app.App`
- :py:class:`betty.project.Project`
- :py:class:`betty.project.extension.Extension`

Extensions always exist in the context of a project, so they are the same level. Additionally, Betty may not be running,
leaving us with three levels:
- global (``None``)
- app (:py:class:`betty.app.App`)
- project (:py:class:`betty.project.Project`)
"""
