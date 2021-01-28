import functools
import inspect
import weakref
from collections import defaultdict, deque
from contextlib import contextmanager, suppress
from copy import copy
from functools import singledispatch
from typing import Any, Union, Callable, Sequence, Tuple, Optional, List, Type, TypeVar, Iterable

from orderedset import OrderedSet

from betty.graph import tsort, Graph
from betty.typing import function


T = TypeVar('T')


class UnsupportedReactive(ValueError):
    pass  # pragma: no cover


def reactive(subject: Optional[Any] = None, *args, **kwargs):
    def decorator(subject: Any):
        return _reactive(subject, *args, **kwargs)
    if subject is None:
        return decorator
    return decorator(subject)


@singledispatch
def _reactive(subject: Optional[Any], *args, **kwargs) -> None:
    raise UnsupportedReactive('%s types cannot be made reactive.' % subject)


# A reactive has an attribute called "react" containing a ReactorController.
# See assert_reactive() and isreactive().
Reactive = Any


Reactor = Callable[[], None]


# A reactor definition is a reactor or anything that can be resolved to its reactors.
ReactorDefinition = Union[Reactor, Reactive]


class ReactorController:
    _trigger_suspended: bool = False
    _chain_is_reacting: bool = False
    _chain_reactor_graph: Graph = defaultdict(OrderedSet)
    _chain_reactors: deque = deque()
    _chain_current_reactor: Optional[Reactor] = None

    def __init__(self):
        self._reactors = []

    def __call__(self, *args, **kwargs):
        self.react(*args, **kwargs)

    def trigger(self) -> None:
        if ReactorController._trigger_suspended:
            return
        if self.trigger == ReactorController._chain_current_reactor:
            return
        self._update_reactor_graph()
        self._trigger_reactor_chain()

    def _update_reactor_graph(self) -> None:
        if len(self._reactors) == 0:
            return
        for reactor in self._reactors:
            for source_reactor, target_reactor in self._expand_reactor(None, reactor):
                ReactorController._chain_reactor_graph[source_reactor].add(target_reactor)
        # The first reactor, which is None, is the current reactor controller, so skip it.
        ReactorController._chain_reactors = deque(tsort(ReactorController._chain_reactor_graph)[1:])
        del ReactorController._chain_reactor_graph[None]

    def _expand_reactor(self, caller: Optional[Reactor], reactor: ReactorDefinition) -> Sequence[Tuple[Optional[Reactor], Reactor]]:
        # weakref.proxy is not hashable, so we use weakref.ref and dereference it ourselves.
        if isinstance(reactor, weakref.ref):
            reactor = reactor()

        if isreactive(reactor):
            yield caller, reactor.react.trigger
            for reactor_reactor in reactor.react._reactors:
                yield from self._expand_reactor(reactor.react.trigger, reactor_reactor)
        else:
            yield caller, reactor

    def _trigger_reactor_chain(self) -> None:
        if ReactorController._chain_is_reacting:
            return
        ReactorController._chain_is_reacting = True
        try:
            while True:
                try:
                    ReactorController._chain_current_reactor = ReactorController._chain_reactors.popleft()
                except IndexError:
                    return
                # Remove outdegree vertices, if they exist. This keeps the graph as small as possible, allowing for the
                # most efficient re-tsorting if it must be extended because of branched reactors.
                with suppress(KeyError):
                    del ReactorController._chain_reactor_graph[ReactorController._chain_current_reactor]
                ReactorController._chain_current_reactor()
        finally:
            ReactorController._chain_is_reacting = False
            ReactorController._chain_current_reactor = None

    def _weakref(self, target, *args, **kwargs) -> weakref.ref:
        if inspect.ismethod(target):
            return weakref.WeakMethod(target, *args, **kwargs)
        # weakref.proxy is not hashable, so we use weakref.ref and dereference it ourselves.
        return weakref.ref(target, *args, **kwargs)

    @classmethod
    @contextmanager
    def suspend(cls) -> None:
        original_suspended = ReactorController._trigger_suspended
        ReactorController._trigger_suspended = True
        yield
        ReactorController._trigger_suspended = original_suspended

    def react(self, *reactors: ReactorDefinition) -> None:
        for reactor in reactors:
            self._reactors.append(reactor)

    def shutdown(self, *reactors: ReactorDefinition) -> None:
        for reactor in reactors:
            self._reactors.remove(reactor)

    def react_weakref(self, *reactors: ReactorDefinition) -> None:
        """
        Add a reactor using a weakref.

        This is a small helper, and it doesn't do much, but it serves as a reminder for people that it's important to
        consider using weakrefs for the performance of their application: if a reactor is added without a weakref, it
        MUST be shut down explicitly or a reference to it will exist forever, consuming memory and potentially slowing
        down reactivity.
        """
        for reactor in reactors:
            self.react(self._weakref(reactor, self._reactors.remove))

    def shutdown_weakref(self, *reactors: ReactorDefinition) -> None:
        for reactor in reactors:
            self.shutdown(self._weakref(reactor, self._reactors.remove))


def assert_reactive(subject, controller_type: Type[ReactorController] = ReactorController) -> None:
    try:
        assert isinstance(getattr(subject, 'react'), controller_type)
    except (AttributeError, AssertionError):
        raise ValueError('%s is not reactive: %s.react does not exist or is not an instance of %s.' % (subject, subject, controller_type))


def isreactive(subject, controller_type: Type[ReactorController] = ReactorController) -> bool:
    with suppress(ValueError):
        assert_reactive(subject, controller_type)
        return True
    return False


class Scope:
    _scope: Optional[List[ReactorDefinition]] = None

    @classmethod
    @contextmanager
    def collect(cls, scoped_reactive: Reactive, scope: List[ReactorDefinition]) -> None:
        cls.clear(scoped_reactive, scope)
        cls.register(scoped_reactive)
        original_scope = cls._scope
        cls._scope = scope
        yield
        cls._scope = original_scope
        for dependency in scope:
            dependency.react.react_weakref(scoped_reactive)

    @classmethod
    def clear(cls, scoped_reactive: Reactive, scope: List[ReactorDefinition]):
        for dependency in scope:
            dependency.react.shutdown_weakref(scoped_reactive)
        scope.clear()

    @classmethod
    def register(cls, scoped_reactive: ReactorDefinition) -> None:
        """
        Register a reactive if it's a dependency for another one.
        """
        if cls._scope is not None:
            cls._scope.append(scoped_reactive)

    @classmethod
    def register_self(cls, decorated_function):
        """
        Register the instance a reactive method is bound to (also known as `self`), if it's a dependency for
        another one.
        """
        @functools.wraps(decorated_function)
        def _register_self(self, *args, **kwargs):
            cls.register(self)
            return decorated_function(self, *args, **kwargs)
        return _register_self


class InstanceAttribute:
    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        raise NotImplementedError


class _FunctionReactorController(ReactorController):
    def __init__(self, on_trigger_call: Optional[callable]):
        super().__init__()
        self._on_trigger_call = on_trigger_call
        self._scope = []

    def trigger(self) -> None:
        if self._on_trigger_call is not None:
            self._on_trigger_call()
        super().trigger()


class _ReactiveFunction(InstanceAttribute):
    def __init__(self, decorated_function: callable, on_trigger_call: bool):
        self._decorated_function = decorated_function
        self._on_trigger_call = on_trigger_call
        self.react = _FunctionReactorController(
            self.__call__ if on_trigger_call else None,
        )

    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        return _FunctionReactorController(
            lambda *args, **kwargs: self._call(instance.react.getattr(self), instance, *args, **kwargs) if self._on_trigger_call else None,
        )

    def __get__(self, instance, owner):
        if instance is None:
            return self

        def call(*args, **kwargs):
            assert_reactive(instance)
            reactive_instance_attribute = instance.react.getattr(self)
            with Scope.collect(reactive_instance_attribute, reactive_instance_attribute.react._scope):
                return self._decorated_function(instance, *args, **kwargs)
        return call

    def __call__(self, *args, **kwargs):
        return self._call(self, *args, **kwargs)

    def _call(self, reactive_function: Reactive, *args, **kwargs):
        with Scope.collect(reactive_function, reactive_function.react._scope):
            return self._decorated_function(*args, **kwargs)


@_reactive.register(function)
def reactive_function(decorated_function, on_trigger_call: bool = False):
    _reactive_function = _ReactiveFunction(decorated_function, on_trigger_call)
    functools.update_wrapper(_reactive_function, decorated_function)
    return _reactive_function


class _ReactivePropertyReactorController(ReactorController):
    def __init__(self, reactive_property: '_ReactiveProperty', instance):
        super().__init__()
        self._reactive_property = reactive_property
        self._instance = instance
        self._scope = []

    def trigger(self) -> None:
        for on_trigger in self._reactive_property._on_trigger:
            on_trigger(self._instance)
        super().trigger()


class _ReactiveProperty(InstanceAttribute):
    def __init__(self, decorated_property: property, on_trigger: Sequence[Callable[[T], None]] = ()):
        if not decorated_property.fget:
            raise UnsupportedReactive('Properties must have a getter to be made reactive.')
        self._decorated_property = decorated_property
        self._on_trigger = on_trigger

    def create_instance_attribute_reactor_controller(self, instance) -> ReactorController:
        return _ReactivePropertyReactorController(self, instance)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return self.__get__from_instance(instance, owner)

    def __get__from_instance(self, instance, owner=None):
        assert_reactive(instance, _InstanceReactorController)
        reactive_instance_attribute = instance.react.getattr(self)
        with Scope.collect(reactive_instance_attribute, reactive_instance_attribute.react._scope):
            return self._decorated_property.__get__(instance, owner)

    def __set__(self, instance, value):
        reactive_instance_attribute = instance.react.getattr(self)
        Scope.clear(reactive_instance_attribute, reactive_instance_attribute.react._scope)
        self._decorated_property.__set__(instance, value)
        if isreactive(value):
            reactive_instance_attribute.react._scope.append(value)
            value.react.react_weakref(reactive_instance_attribute)
        reactive_instance_attribute.react.trigger()

    def __delete__(self, instance):
        reactive_instance_attribute = instance.react.getattr(self)
        Scope.clear(reactive_instance_attribute, reactive_instance_attribute.react._scope)
        self._decorated_property.__delete__(instance)
        instance.react.getattr(self).react.trigger()

    def setter(self, *args, **kwargs):
        return _ReactiveProperty(self._decorated_property.setter(*args, **kwargs))

    def deleter(self, *args, **kwargs):
        return _ReactiveProperty(self._decorated_property.deleter(*args, **kwargs))


class _ReactiveInstanceAttribute:
    def __init__(self, reactor_controller: ReactorController):
        self.react = reactor_controller


class _InstanceReactorController(ReactorController):
    def __init__(self, instance):
        super().__init__()
        self._instance = instance
        self._reactive_attributes = {}

        # Initialize each reactive instance attribute and autowire it. Get the attributes through the class, though, so
        # we can get the actual descriptors.
        for name, attribute in inspect.getmembers(instance.__class__, self._isreactive):
            if isinstance(attribute, InstanceAttribute):
                reactor_controller = attribute.create_instance_attribute_reactor_controller(instance)
            else:
                reactor_controller = ReactorController()
            reactive_attribute = _ReactiveInstanceAttribute(reactor_controller)
            reactive_attribute.react(instance)
            self._reactive_attributes[name] = self._reactive_attributes[attribute] = reactive_attribute

    def _isreactive(self, attribute) -> bool:
        if isreactive(attribute):
            return True

        if isinstance(attribute, InstanceAttribute):
            return True

        return False

    def getattr(self, name_or_attribute) -> Reactive:
        """
        Get a reactive instance attribute.
        """
        try:
            return self._reactive_attributes[name_or_attribute]
        except KeyError:
            raise AttributeError('No reactive attribute "%s" exists.' % name_or_attribute)


@_reactive.register(type)
def reactive_instance(decorated_class) -> type:
    # Override the initializer to instantiate an instance-level reactor controller.
    original_init = decorated_class.__init__

    def init(self, *args, **kwargs):
        self.react = _InstanceReactorController(self)
        original_init(self, *args, **kwargs)

    decorated_class.__init__ = init

    return decorated_class


@_reactive.register(property)
def reactive_property(decorated_property, on_trigger: Sequence[Callable[[T], None]] = ()):
    _reactive_property = _ReactiveProperty(decorated_property, on_trigger)
    functools.update_wrapper(_reactive_property, decorated_property)
    return _reactive_property


# @todo We require ordering within Betty, which wans't guaranteed until Python 3.7.
# @todo However, dict and OrderedDict behave differently so maybe dump Python 3.6 support
# @todo since by the time Betty 0.3.0 will come out there likely won't be more than 6 months until 3.6's EOL anyway.
class ReactiveDict(dict):
    def __init__(self, *args, **kwargs):
        self.react = ReactorController()
        super().__init__(*args, **kwargs)
        for value in dict.values(self):
            self._wire(value)

    def _wire(self, value) -> None:
        if isreactive(value):
            value.react(self)

    def _unwire(self, value) -> None:
        if isreactive(value):
            value.react.shutdown(self)

    def clear(self) -> None:
        for value in dict.values(self):
            self._unwire(value)
        super().clear()
        self.react.trigger()

    @Scope.register_self
    def get(self, key):
        return super().get(key)

    @Scope.register_self
    def items(self):
        return super().items()

    @Scope.register_self
    def keys(self):
        return super().keys()

    def pop(self, key):
        value = super().pop(key)
        self._unwire(value)
        self.react.trigger()
        return value

    def popitem(self):
        key, value = super().popitem()
        self._unwire(value)
        self.react.trigger()
        return key, value

    def setdefault(self, key, value):
        try:
            return self[key]
        except KeyError:
            self[key] = value
            return value

    def update(self, other) -> None:
        for value in super().values():
            self._unwire(value)
        super().update(other)
        for value in super().values():
            self._wire(value)
        self.react.trigger()

    @Scope.register_self
    def values(self):
        return super().values()

    @Scope.register_self
    def __contains__(self, item):
        return super().__contains__(item)

    def __delitem__(self, key):
        with suppress(KeyError):
            self._unwire(super().__getitem__(key))
        super().__delitem__(key)
        self.react.trigger()

    @Scope.register_self
    def __eq__(self, other):
        return super().__eq__(other)

    @Scope.register_self
    def __getitem__(self, item):
        return super().__getitem__(item)

    @Scope.register_self
    def __iter__(self):
        return super().__iter__()

    @Scope.register_self
    def __len__(self):
        return super().__len__()

    @Scope.register_self
    def __ne__(self, other):
        return super().__ne__(other)

    if hasattr(dict, '__reversed__'):
        @Scope.register_self
        def __reversed__(self):
            return super().__reversed__()

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self._wire(value)
        self.react.trigger()

    @Scope.register_self
    def __sizeof__(self):
        return super().__sizeof__()


class ReactiveList(list):
    def __init__(self, *args, **kwargs):
        self.react = ReactorController()
        super().__init__(*args, **kwargs)
        for value in list.__iter__(self):
            self._wire(value)

    def _wire(self, value) -> None:
        if isreactive(value):
            value.react(self)

    def _unwire(self, value) -> None:
        if isreactive(value):
            value.react.shutdown(self)

    def append(self, value) -> None:
        super().append(value)
        self._wire(value)
        self.react.trigger()

    def clear(self) -> None:
        for value in list.__iter__(self):
            self._unwire(value)
        super().clear()
        self.react.trigger()

    @Scope.register_self
    def copy(self) -> 'ReactiveList':
        return copy(self)

    @Scope.register_self
    def count(self, value) -> int:
        return super().count(value)

    def extend(self, other: Iterable) -> None:
        for value in other:
            super().append(value)
            self._wire(value)
        self.react.trigger()

    @Scope.register_self
    def index(self, value, *args, **kwargs) -> int:
        return super().index(value, *args, **kwargs)

    def insert(self, index: int, value) -> None:
        super().insert(index, value)
        self._wire(value)
        self.react.trigger()

    def pop(self, *args, **kwargs) -> Any:
        value = super().pop(*args, **kwargs)
        self._unwire(value)
        self.react.trigger()
        return value

    def remove(self, value) -> None:
        super().remove(value)
        self._unwire(value)
        self.react.trigger()

    def reverse(self) -> None:
        super().reverse()
        self.react.trigger()

    def sort(self, *args, **kwargs) -> None:
        super().sort(*args, **kwargs)
        self.react.trigger()

    def __add__(self, other):
        return ReactiveList(super().__add__(other))

    @Scope.register_self
    def __contains__(self, value) -> bool:
        return super().__contains__(value)

    def __delitem__(self, index) -> None:
        with suppress(IndexError):
            self._unwire(super().__getitem__(index))
        super().__delitem__(index)
        self.react.trigger()

    @Scope.register_self
    def __eq__(self, other) -> bool:
        return super().__eq__(other)

    @Scope.register_self
    def __getitem__(self, index) -> Any:
        return super().__getitem__(index)

    @Scope.register_self
    def __iadd__(self, other: Iterable) -> 'ReactiveList':
        for value in other:
            super().append(value)
            self._wire(value)
        self.react.trigger()
        return self

    @Scope.register_self
    def __imul__(self, other) -> 'ReactiveList':
        for value in list.__iter__(self):
            self._unwire(value)
        super().__imul__(other)
        for value in list.__iter__(self):
            self._wire(value)
        self.react.trigger()
        return self

    @Scope.register_self
    def __iter__(self):
        return super().__iter__()

    @Scope.register_self
    def __len__(self):
        return super().__len__()

    def __mul__(self, other):
        return ReactiveList(super().__mul__(other))

    @Scope.register_self
    def __ne__(self, other):
        return super().__ne__(other)

    @Scope.register_self
    def __reversed__(self):
        return super().__reversed__()

    def __rmul__(self, other):
        return ReactiveList(super().__rmul__(other))

    def __setitem__(self, index, value):
        super().__setitem__(index, value)
        self._wire(value)
        self.react.trigger()

    @Scope.register_self
    def __sizeof__(self):
        return super().__sizeof__()
