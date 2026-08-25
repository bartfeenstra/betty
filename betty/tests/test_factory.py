from typing import Any, Self, override

import pytest

from betty.factory import Factory, Manufacturable, Manufacturer, UnsupportedManufacturer
from betty.service_level import ServiceLevel


class _Manufacturer:
    pass


class _ManufacturerWithoutServicesWithOptionalInitArguments:
    def __init__(self, arg: Any = None, /, *, kwarg: Any = None):
        assert arg is None
        assert kwarg is None


class _ManufacturerWithoutServicesWithRequiredInitArguments:
    def __init__(self, arg: Any, /, *, kwarg: Any):
        raise NotImplementedError


class _ManufacturerWithoutServicesWithVariadicInitArguments:
    def __init__(self, *args: Any, **kwargs: Any):
        assert not args
        assert not kwargs


class _ManufacturerWithNamedServicesWithOptionalInitArguments:
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


class _ManufacturerWithNamedServicesWithRequiredInitArguments:
    def __init__(
        self,
        services,  # noqa: ANN001
        arg: Any,
        /,
        *,
        kwarg: Any,
    ):
        raise NotImplementedError


class _ManufacturerWithNamedServicesWithVariadicInitArguments:
    def __init__(
        self,
        services,  # noqa: ANN001
        *args: Any,
        **kwargs: Any,
    ):
        assert isinstance(services, ServiceLevel)
        assert not args
        assert not kwargs


class _ManufacturerWithTypedServicesWithOptionalInitArguments:
    def __init__(self, _: ServiceLevel, arg: Any = None, /, *, kwarg: Any = None):
        assert isinstance(_, ServiceLevel)
        assert arg is None
        assert kwarg is None


class _ManufacturerWithTypedServicesWithRequiredInitArguments:
    def __init__(self, _: ServiceLevel, arg: Any, /, *, kwarg: Any):
        raise NotImplementedError


class _ManufacturerWithTypedServicesWithVariadicInitArguments:
    def __init__(self, _: ServiceLevel, *args: Any, **kwargs: Any):
        assert isinstance(_, ServiceLevel)
        assert not args
        assert not kwargs


class _Manufacturable(Manufacturable):
    @override
    @classmethod
    async def new(cls, services: ServiceLevel, /) -> Self:
        return cls()


def _sync_callable_manufacturer_without_services() -> _Manufacturer:
    return _Manufacturer()


def _sync_callable_manufacturer_without_services_with_optional_arguments(
    arg: Any = None, /, *, kwarg: Any = None
) -> _Manufacturer:
    return _Manufacturer()


def _sync_callable_manufacturer_without_services_with_required_arguments(
    arg: Any, /, *, kwarg: Any
) -> _Manufacturer:
    raise NotImplementedError


def _sync_callable_manufacturer_without_services_with_variadic_arguments(
    *args: Any, **kwargs: Any
) -> _Manufacturer:
    return _Manufacturer()


def _sync_callable_manufacturer_with_services(
    services: ServiceLevel, /
) -> _Manufacturer:
    return _Manufacturer()


def _sync_callable_manufacturer_with_services_with_optional_arguments(
    services: ServiceLevel, arg: Any = None, /, *, kwarg: Any = None
) -> _Manufacturer:
    return _Manufacturer()


def _sync_callable_manufacturer_with_services_with_required_arguments(
    services: ServiceLevel, arg: Any, /, *, kwarg: Any
) -> _Manufacturer:
    raise NotImplementedError


def _sync_callable_manufacturer_with_services_with_variadic_arguments(
    services: ServiceLevel, *args: Any, **kwargs: Any
) -> _Manufacturer:
    return _Manufacturer()


async def _async_callable_manufacturer_without_services() -> _Manufacturer:
    return _Manufacturer()


async def _async_callable_manufacturer_without_services_with_optional_arguments(
    arg: Any = None, /, *, kwarg: Any = None
) -> _Manufacturer:
    return _Manufacturer()


async def _async_callable_manufacturer_without_services_with_required_arguments(
    arg: Any, /, *, kwarg: Any
) -> _Manufacturer:
    raise NotImplementedError


async def _async_callable_manufacturer_without_services_with_variadic_arguments(
    *args: Any, **kwargs: Any
) -> _Manufacturer:
    return _Manufacturer()


async def _async_callable_manufacturer_with_services(
    services: ServiceLevel, /
) -> _Manufacturer:
    return _Manufacturer()


async def _async_callable_manufacturer_with_services_with_optional_arguments(
    services: ServiceLevel, arg: Any = None, /, *, kwarg: Any = None
) -> _Manufacturer:
    return _Manufacturer()


async def _async_callable_manufacturer_with_services_with_required_arguments(
    services: ServiceLevel, arg: Any, /, *, kwarg: Any
) -> _Manufacturer:
    raise NotImplementedError


async def _async_callable_manufacturer_with_services_with_variadic_arguments(
    services: ServiceLevel, *args: Any, **kwargs: Any
) -> _Manufacturer:
    return _Manufacturer()


class TestFactory:
    @pytest.mark.parametrize(
        ("expected", "manufacturer"),
        [
            (_Manufacturer, _Manufacturer),
            (
                _ManufacturerWithoutServicesWithOptionalInitArguments,
                _ManufacturerWithoutServicesWithOptionalInitArguments,
            ),
            (
                _ManufacturerWithoutServicesWithVariadicInitArguments,
                _ManufacturerWithoutServicesWithVariadicInitArguments,
            ),
            (
                _ManufacturerWithNamedServicesWithOptionalInitArguments,
                _ManufacturerWithNamedServicesWithOptionalInitArguments,
            ),
            (
                _ManufacturerWithNamedServicesWithVariadicInitArguments,
                _ManufacturerWithNamedServicesWithVariadicInitArguments,
            ),
            (
                _ManufacturerWithTypedServicesWithOptionalInitArguments,
                _ManufacturerWithTypedServicesWithOptionalInitArguments,
            ),
            (
                _ManufacturerWithTypedServicesWithVariadicInitArguments,
                _ManufacturerWithTypedServicesWithVariadicInitArguments,
            ),
            (_Manufacturable, _Manufacturable),
            (_Manufacturer, _sync_callable_manufacturer_without_services),
            (
                _Manufacturer,
                _sync_callable_manufacturer_without_services_with_optional_arguments,
            ),
            (
                _Manufacturer,
                _sync_callable_manufacturer_without_services_with_variadic_arguments,
            ),
            (_Manufacturer, _sync_callable_manufacturer_with_services),
            (
                _Manufacturer,
                _sync_callable_manufacturer_with_services_with_optional_arguments,
            ),
            (
                _Manufacturer,
                _sync_callable_manufacturer_with_services_with_variadic_arguments,
            ),
            (_Manufacturer, _async_callable_manufacturer_without_services),
            (
                _Manufacturer,
                _async_callable_manufacturer_without_services_with_optional_arguments,
            ),
            (
                _Manufacturer,
                _async_callable_manufacturer_without_services_with_variadic_arguments,
            ),
            (_Manufacturer, _async_callable_manufacturer_with_services),
            (
                _Manufacturer,
                _async_callable_manufacturer_with_services_with_optional_arguments,
            ),
            (
                _Manufacturer,
                _async_callable_manufacturer_with_services_with_variadic_arguments,
            ),
        ],
    )
    async def test_new__should_create(
        self, expected: type[_Manufacturer], manufacturer: Manufacturer
    ) -> None:
        assert isinstance(await Factory(ServiceLevel()).new(manufacturer), expected)

    @pytest.mark.parametrize(
        "manufacturer",
        [
            _ManufacturerWithoutServicesWithRequiredInitArguments,
            _ManufacturerWithNamedServicesWithRequiredInitArguments,
            _ManufacturerWithTypedServicesWithRequiredInitArguments,
            _sync_callable_manufacturer_without_services_with_required_arguments,
            _sync_callable_manufacturer_with_services_with_required_arguments,
            _async_callable_manufacturer_without_services_with_required_arguments,
            _async_callable_manufacturer_with_services_with_required_arguments,
        ],
    )
    async def test_new__should_raise_unsupported_manufacturer(
        self, manufacturer: Manufacturer
    ) -> None:
        with pytest.raises(UnsupportedManufacturer):
            await Factory(ServiceLevel()).new(manufacturer)
