"""
Service provider levels.
"""

from typing import TypeAlias

from betty.app import App
from betty.project import Project

ServiceProviderLevel: TypeAlias = None | App | Project
"""
A service provider level.

A runtime Betty application consists of three types of service providers:

- :py:class:`betty.app.App`
- :py:class:`betty.project.Project`
- :py:class:`betty.project.extension.Extension`

Extensions always exist in the context of a project, so they are the same level. Additionally, Betty may not be running,
leaving us with three levels:
- global (``None``)
- app (:py:class:`betty.app.App`)
- project (:py:class:`betty.project.Project`)
"""
