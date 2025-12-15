"""
Test utilities for :py:mod:`betty.config.factory`.
"""

from typing import Generic, TypeVar

import pytest

from betty.app import App
from betty.config import Configuration
from betty.config.factory import ConfigurationDependentSelfFactory
from betty.factory import FactoryError, new_target
from betty.project import Project
from betty.requirement import HasRequirement, Requirement

_ConfigurationT = TypeVar("_ConfigurationT", bound=Configuration)


class ConfigurationDependentSelfFactoryTestBase(Generic[_ConfigurationT]):
    """
    A base class for testing :py:class:`betty.config.factory.ConfigurationDependentSelfFactory` implementations.
    """

    @pytest.fixture
    def configuration_dependent_self_factory_sut(
        self,
    ) -> type[ConfigurationDependentSelfFactory[_ConfigurationT]]:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    @pytest.fixture
    def configuration_dependent_self_factory_sut_configuration(
        self,
    ) -> _ConfigurationT:
        """
        Provide the system(s) under test.
        """
        raise NotImplementedError

    async def test_new_for_configuration__with_global(
        self,
        configuration_dependent_self_factory_sut: type[
            ConfigurationDependentSelfFactory[_ConfigurationT]
        ],
        configuration_dependent_self_factory_sut_configuration: _ConfigurationT,
    ) -> None:
        """
        Tests :py:meth:`betty.config.factory.ConfigurationDependentSelfFactory.new_for_configuration` implementations.
        """
        try:
            sut = await new_target(
                configuration_dependent_self_factory_sut.new_for_configuration(
                    configuration_dependent_self_factory_sut_configuration
                )
            )
        except FactoryError as error:
            requirement: Requirement | None = None
            if issubclass(configuration_dependent_self_factory_sut, HasRequirement):
                requirement = (
                    await configuration_dependent_self_factory_sut.requirement(None)
                )
            if requirement is None:
                raise AssertionError(
                    f"{configuration_dependent_self_factory_sut} fails to be created through the global factory but does not declare any global requirements"
                ) from error
        else:
            assert (
                sut.configuration
                is configuration_dependent_self_factory_sut_configuration
            )

    async def test_new_for_configuration__with_app(
        self,
        configuration_dependent_self_factory_sut: type[
            ConfigurationDependentSelfFactory[_ConfigurationT]
        ],
        configuration_dependent_self_factory_sut_configuration: _ConfigurationT,
        isolated_app: App,
    ) -> None:
        """
        Tests :py:meth:`betty.config.factory.ConfigurationDependentSelfFactory.new_for_configuration` implementations.
        """
        try:
            await isolated_app.new_target(
                configuration_dependent_self_factory_sut.new_for_configuration(
                    configuration_dependent_self_factory_sut_configuration
                )
            )
        except FactoryError as error:
            requirement: Requirement | None = None
            if issubclass(configuration_dependent_self_factory_sut, HasRequirement):
                requirement = (
                    await configuration_dependent_self_factory_sut.requirement(
                        isolated_app
                    )
                )
            if requirement is None:
                raise AssertionError(
                    f"{configuration_dependent_self_factory_sut} fails to be created through the app factory but does not declare any app requirements"
                ) from error

    async def test_new_for_configuration__with_project(
        self,
        configuration_dependent_self_factory_sut: type[
            ConfigurationDependentSelfFactory[_ConfigurationT]
        ],
        configuration_dependent_self_factory_sut_configuration: _ConfigurationT,
        isolated_app: App,
    ) -> None:
        """
        Tests :py:meth:`betty.config.factory.ConfigurationDependentSelfFactory.new_for_configuration` implementations.
        """
        async with Project.new_isolated(isolated_app) as project, project:
            try:
                await project.new_target(
                    configuration_dependent_self_factory_sut.new_for_configuration(
                        configuration_dependent_self_factory_sut_configuration
                    )
                )
            except FactoryError as error:
                requirement: Requirement | None = None
                if issubclass(configuration_dependent_self_factory_sut, HasRequirement):
                    requirement = (
                        await configuration_dependent_self_factory_sut.requirement(
                            project
                        )
                    )
                if requirement is None:
                    raise AssertionError(
                        f"{configuration_dependent_self_factory_sut} fails to be created through the project factory but does not declare any project requirements"
                    ) from error
