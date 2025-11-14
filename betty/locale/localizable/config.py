"""
Provide localizable configuration.
"""

from abc import abstractmethod
from contextlib import suppress
from typing import Any, Generic, Self, TypeVar, cast, final, overload

from typing_extensions import override

from betty.assertion import AssertionChain
from betty.config import Configuration
from betty.importlib import fully_qualified_name
from betty.locale import UNDETERMINED_LOCALE
from betty.locale.localizable import (
    Localizable,
    LocalizableLike,
    Plain,
    StaticTranslations,
    _,
    ensure_localizable,
)
from betty.locale.localizable.assertion import assert_static_translations
from betty.serde.dump import Dump, NotDumpable

_T = TypeVar("_T")
_LocalizableT = TypeVar("_LocalizableT")


@final
class LocalizableConfiguration(Configuration):
    """
    Configuration for a :py:class:`betty.locale.localizable.Localizable`.
    """

    def __init__(self, localizable: LocalizableLike, /):
        super().__init__()
        self.localizable = localizable  # type: ignore[assignment]

    @property
    def localizable(self) -> Localizable:
        """
        The configured localizable.
        """
        return self._localizable

    @localizable.setter
    def localizable(self, localizable: LocalizableLike) -> None:
        self._localizable = ensure_localizable(localizable)

    @override
    def load(self, dump: Dump, /) -> None:
        self._localizable = StaticTranslations(assert_static_translations()(dump))

    @override
    def dump(self) -> Dump:
        localizable = self._localizable
        if isinstance(localizable, Plain):
            localizable = StaticTranslations(
                {
                    localizable.locale: localizable.text,
                }
            )
        if isinstance(localizable, StaticTranslations):
            translations = localizable.translations
            if len(translations) == 1:
                with suppress(KeyError):
                    return translations[UNDETERMINED_LOCALE]
            return dict(translations)
        raise NotDumpable(
            _(
                "Only plain text and static translations can be dumped to configuration, not `{localizable}` objects."
            ).format(localizable=fully_qualified_name(type(localizable)))
        )


class _LocalizableConfigurationAttr(Generic[_LocalizableT]):
    def __init__(self, attr_name: str, /):
        self._attr_name = f"_{attr_name}"

    def __set__(self, instance: object, value: LocalizableLike, /) -> None:
        configuration = self._get_configuration(instance)
        if configuration:
            configuration.localizable = value  # type: ignore[assignment]
        else:
            configuration = LocalizableConfiguration(value)
            setattr(instance, self._attr_name, configuration)

    @overload
    def __get__(self, instance: None, owner: type[object], /) -> Self:
        pass

    @overload
    def __get__(self, instance: _T, owner: type[_T], /) -> _LocalizableT:
        pass

    def __get__(
        self, instance: object | None, owner: type[object], /
    ) -> _LocalizableT | Self:
        if instance is None:
            return self  # type: ignore[return-value]
        return self._get(instance)

    @abstractmethod
    def _get(self, instance: object, /) -> _LocalizableT:
        pass

    def _get_configuration(self, instance: object) -> LocalizableConfiguration | None:
        return cast(
            LocalizableConfiguration | None, getattr(instance, self._attr_name, None)
        )

    @abstractmethod
    def _ensure_configuration(self, instance: object) -> LocalizableConfiguration:
        pass

    def assert_load(self, instance: object, /) -> AssertionChain[Any, None]:
        return AssertionChain(
            lambda dump: self._ensure_configuration(instance).load(dump)
        )

    @abstractmethod
    def dump(self, instance: object, /) -> Dump:
        pass


@final
class RequiredLocalizableConfigurationAttrNotInitialized(ValueError):
    """
    Raised when a class failed to initialize a value for its :py:class:`betty.locale.localizable.config.RequiredLocalizableConfigurationAttr`.
    """


@final
class RequiredLocalizableConfigurationAttr(_LocalizableConfigurationAttr[Localizable]):
    """
    An attribute for required configuration for a :py:class:`betty.locale.localizable.Localizable`.
    """

    @override
    def _get(self, instance: object, /) -> Localizable:
        return self._ensure_configuration(instance).localizable

    @override
    def _ensure_configuration(self, instance: object) -> LocalizableConfiguration:
        configuration = self._get_configuration(instance)
        if configuration is None:
            instance_name = fully_qualified_name(type(instance))
            raise RequiredLocalizableConfigurationAttrNotInitialized(
                f"{instance_name}.{self._attr_name[1:]} was never initialized. {instance_name}.__init__() MUST set a value."
            )
        return configuration

    @override
    def dump(self, instance: object, /) -> Dump:
        return self._ensure_configuration(instance).dump()


@final
class OptionalLocalizableConfigurationAttr(
    _LocalizableConfigurationAttr[Localizable | None]
):
    """
    An attribute for optional configuration for a :py:class:`betty.locale.localizable.Localizable`.
    """

    @override
    def __set__(self, instance: object, value: LocalizableLike | None, /) -> None:
        if value is None:
            self.__delete__(instance)
        else:
            super().__set__(instance, value)

    def __delete__(self, instance: object) -> None:
        delattr(instance, self._attr_name)

    @override
    def _get(self, instance: object, /) -> Localizable | None:
        configuration = self._get_configuration(instance)
        if configuration is None:
            return None
        return configuration.localizable

    @override
    def _ensure_configuration(self, instance: object) -> LocalizableConfiguration:
        configuration = self._get_configuration(instance)
        if configuration is None:
            configuration = LocalizableConfiguration(Plain(""))
            setattr(instance, self._attr_name, configuration)
        return configuration

    @override
    def dump(self, instance: object, /) -> Dump:
        configuration = self._get_configuration(instance)
        if configuration is None:
            return None
        return configuration.dump()
