from typing import Any, Self, override

import pytest

from betty.factory import Factory, FactoryTarget, Manufacturable, UnsupportedTarget
from betty.service_level import ServiceLevel


class _Target:
    pass


class _TargetWithoutServicesWithOptionalInitArguments:
    def __init__(self, arg: Any = None, /, *, kwarg: Any = None):
        assert arg is None
        assert kwarg is None


class _TargetWithoutServicesWithRequiredInitArguments:
    def __init__(self, arg: Any, /, *, kwarg: Any):
        raise NotImplementedError


class _TargetWithoutServicesWithVariadicInitArguments:
    def __init__(self, *args: Any, **kwargs: Any):
        assert not args
        assert not kwargs


class _TargetWithNamedServicesWithOptionalInitArguments:
    def __init__(
        self,
        services,  # noqa: ANN001
        arg: Any = None,
        /,
        *,
        kwarg: Any = None,
    ):
        assert isinstance(services, ServiceLevel)
        assert arg is None
        assert kwarg is None


class _TargetWithNamedServicesWithRequiredInitArguments:
    def __init__(
        self,
        services,  # noqa: ANN001
        arg: Any,
        /,
        *,
        kwarg: Any,
    ):
        raise NotImplementedError


class _TargetWithNamedServicesWithVariadicInitArguments:
    def __init__(
        self,
        services,  # noqa: ANN001
        *args: Any,
        **kwargs: Any,
    ):
        assert isinstance(services, ServiceLevel)
        assert not args
        assert not kwargs


class _TargetWithTypedServicesWithOptionalInitArguments:
    def __init__(self, _: ServiceLevel, arg: Any = None, /, *, kwarg: Any = None):
        assert isinstance(_, ServiceLevel)
        assert arg is None
        assert kwarg is None


class _TargetWithTypedServicesWithRequiredInitArguments:
    def __init__(self, _: ServiceLevel, arg: Any, /, *, kwarg: Any):
        raise NotImplementedError


class _TargetWithTypedServicesWithVariadicInitArguments:
    def __init__(self, _: ServiceLevel, *args: Any, **kwargs: Any):
        assert isinstance(_, ServiceLevel)
        assert not args
        assert not kwargs


class _ManufacturableTarget(Manufacturable):
    @override
    @classmethod
    async def new(cls, services: ServiceLevel, /) -> Self:
        return cls()


def _sync_callable_target_without_services() -> _Target:
    return _Target()


def _sync_callable_target_without_services_with_optional_arguments(
    arg: Any = None, /, *, kwarg: Any = None
) -> _Target:
    return _Target()


def _sync_callable_target_without_services_with_required_arguments(
    arg: Any, /, *, kwarg: Any
) -> _Target:
    raise NotImplementedError


def _sync_callable_target_without_services_with_variadic_arguments(
    *args: Any, **kwargs: Any
) -> _Target:
    return _Target()


def _sync_callable_target_with_services(services: ServiceLevel, /) -> _Target:
    return _Target()


def _sync_callable_target_with_services_with_optional_arguments(
    services: ServiceLevel, arg: Any = None, /, *, kwarg: Any = None
) -> _Target:
    return _Target()


def _sync_callable_target_with_services_with_required_arguments(
    services: ServiceLevel, arg: Any, /, *, kwarg: Any
) -> _Target:
    raise NotImplementedError


def _sync_callable_target_with_services_with_variadic_arguments(
    services: ServiceLevel, *args: Any, **kwargs: Any
) -> _Target:
    return _Target()


async def _async_callable_target_without_services() -> _Target:
    return _Target()


async def _async_callable_target_without_services_with_optional_arguments(
    arg: Any = None, /, *, kwarg: Any = None
) -> _Target:
    return _Target()


async def _async_callable_target_without_services_with_required_arguments(
    arg: Any, /, *, kwarg: Any
) -> _Target:
    raise NotImplementedError


async def _async_callable_target_without_services_with_variadic_arguments(
    *args: Any, **kwargs: Any
) -> _Target:
    return _Target()


async def _async_callable_target_with_services(services: ServiceLevel, /) -> _Target:
    return _Target()


async def _async_callable_target_with_services_with_optional_arguments(
    services: ServiceLevel, arg: Any = None, /, *, kwarg: Any = None
) -> _Target:
    return _Target()


async def _async_callable_target_with_services_with_required_arguments(
    services: ServiceLevel, arg: Any, /, *, kwarg: Any
) -> _Target:
    raise NotImplementedError


async def _async_callable_target_with_services_with_variadic_arguments(
    services: ServiceLevel, *args: Any, **kwargs: Any
) -> _Target:
    return _Target()


class TestFactory:
    @pytest.mark.parametrize(
        ("expected", "target"),
        [
            (_Target, _Target),
            (
                _TargetWithoutServicesWithOptionalInitArguments,
                _TargetWithoutServicesWithOptionalInitArguments,
            ),
            (
                _TargetWithoutServicesWithVariadicInitArguments,
                _TargetWithoutServicesWithVariadicInitArguments,
            ),
            (
                _TargetWithNamedServicesWithOptionalInitArguments,
                _TargetWithNamedServicesWithOptionalInitArguments,
            ),
            (
                _TargetWithNamedServicesWithVariadicInitArguments,
                _TargetWithNamedServicesWithVariadicInitArguments,
            ),
            (
                _TargetWithTypedServicesWithOptionalInitArguments,
                _TargetWithTypedServicesWithOptionalInitArguments,
            ),
            (
                _TargetWithTypedServicesWithVariadicInitArguments,
                _TargetWithTypedServicesWithVariadicInitArguments,
            ),
            (_ManufacturableTarget, _ManufacturableTarget),
            (_Target, _sync_callable_target_without_services),
            (_Target, _sync_callable_target_without_services_with_optional_arguments),
            (_Target, _sync_callable_target_without_services_with_variadic_arguments),
            (_Target, _sync_callable_target_with_services),
            (_Target, _sync_callable_target_with_services_with_optional_arguments),
            (_Target, _sync_callable_target_with_services_with_variadic_arguments),
            (_Target, _async_callable_target_without_services),
            (_Target, _async_callable_target_without_services_with_optional_arguments),
            (_Target, _async_callable_target_without_services_with_variadic_arguments),
            (_Target, _async_callable_target_with_services),
            (_Target, _async_callable_target_with_services_with_optional_arguments),
            (_Target, _async_callable_target_with_services_with_variadic_arguments),
        ],
    )
    async def test_new__should_create(
        self, expected: type[_Target], target: FactoryTarget
    ) -> None:
        assert isinstance(await Factory(ServiceLevel()).new(target), expected)

    @pytest.mark.parametrize(
        "target",
        [
            _TargetWithoutServicesWithRequiredInitArguments,
            _TargetWithNamedServicesWithRequiredInitArguments,
            _TargetWithTypedServicesWithRequiredInitArguments,
            _sync_callable_target_without_services_with_required_arguments,
            _sync_callable_target_with_services_with_required_arguments,
            _async_callable_target_without_services_with_required_arguments,
            _async_callable_target_with_services_with_required_arguments,
        ],
    )
    async def test_new__should_raise_unsupported_target(
        self, target: FactoryTarget
    ) -> None:
        with pytest.raises(UnsupportedTarget):
            await Factory(ServiceLevel()).new(target)
