import gc
import sys
import unittest
from contextlib import contextmanager
from typing import Union
from unittest import TestCase

from betty.react import reactive, ReactorController, _InstanceReactorController, UnsupportedReactive, Scope, \
    isreactive, Reactive, Reactor, ReactorDefinition, ReactiveDict, ReactiveList


class ReactiveTestCase(TestCase):
    class _Reactive:
        def __init__(self):
            self.react = ReactorController()

    def _assert_reactor(self, reactor: Reactor, sut: Union[Reactive, ReactorController, None] = None) -> Union[Reactor, None]:
        if sut is not None:
            if not isinstance(sut, ReactorController):
                sut = sut.react
            sut.react(reactor)
            yield None
            sut.shutdown(reactor)
        else:
            yield reactor

    @contextmanager
    def assert_reactor_called(self, sut: Union[Reactive, ReactorController, None] = None) -> Union[Reactor, None]:
        def reactor() -> None:
            if reactor.called:
                self.fail('Failed asserting that a reactor (%s) was called only once.' % reactor)
            reactor.called = True
        reactor.called = False
        yield from self._assert_reactor(reactor, sut)
        self.assertTrue(reactor.called, 'Failed asserting that a reactor (%s) was called, but it was actually never called at all.' % reactor)

    @contextmanager
    def assert_not_reactor_called(self, sut: Union[Reactive, ReactorController, None] = None) -> Union[Reactor, None]:
        def reactor() -> None:
            self.fail('Failed asserting that a reactor (%s) was not called.' % reactor)
        yield from self._assert_reactor(reactor, sut)

    @contextmanager
    def assert_scope_empty(self):
        scope = []
        with Scope.collect(self._Reactive(), scope):
            yield
        self.assertEquals([], scope)

    @contextmanager
    def assert_in_scope(self, dependency: ReactorDefinition):
        scope = []
        with Scope.collect(self._Reactive(), scope):
            yield
        self.assertIn(dependency, scope)

    def assert_is_reactive(self, subject):
        self.assertTrue(isreactive(subject))


class ReactiveTest(TestCase):
    def test_with_unsupported_reactive(self) -> None:
        with self.assertRaises(UnsupportedReactive):
            reactive(999)


class ReactorControllerTest(ReactiveTestCase):
    def test_react_without_reactors(self) -> None:
        sut = ReactorController()
        sut.trigger()

    def test_react_with_reactor(self) -> None:
        sut = ReactorController()
        with self.assert_reactor_called() as reactor:
            sut.react(reactor)
            sut.trigger()

    def test_react_with_diamond_reactors(self) -> None:
        sut = ReactorController()
        with self.assert_reactor_called() as final_reactor:
            intermediate_reactive_1 = self._Reactive()
            intermediate_reactive_2 = self._Reactive()
            intermediate_reactive_1.react(final_reactor)
            intermediate_reactive_2.react(final_reactor)
            sut.react(intermediate_reactive_1)
            sut.react(intermediate_reactive_2)
            sut.trigger()

    def test_react_with_intermediate_diamond_reactors(self) -> None:
        order_tracker = []
        r_a = self._Reactive()
        r_a.react(lambda: order_tracker.append('r_a'))
        r_b = self._Reactive()
        r_b.react(lambda: order_tracker.append('r_b'))
        r_c = self._Reactive()
        r_c.react(lambda: order_tracker.append('r_c'))
        r_d = self._Reactive()
        r_d.react(lambda: order_tracker.append('r_d'))
        r_da = self._Reactive()
        r_da.react(lambda: order_tracker.append('r_da'))
        r_e = self._Reactive()
        r_e.react(lambda: order_tracker.append('r_e'))

        r_a.react(r_b)
        r_b.react(r_c)
        r_b.react(r_d)

        # This is the intermediate trigger we are asserting is consolidated into the reactor chain.
        def f_ca():
            order_tracker.append('f_ca')
            r_e.react.trigger()
        r_c.react(f_ca)
        r_d.react(r_da)
        r_da.react(r_e)

        r_a.react.trigger()
        self.assertEquals(['r_a', 'r_b', 'r_c', 'f_ca', 'r_d', 'r_da', 'r_e'], order_tracker)

    def test_react_using_shortcut_with_reactor(self) -> None:
        sut = ReactorController()
        with self.assert_reactor_called() as reactor:
            sut(reactor)
            sut.trigger()

    def test_shutdown(self) -> None:
        sut = ReactorController()
        with self.assert_reactor_called() as reactor:
            sut.react(reactor)
            sut.trigger()
            sut.shutdown(reactor)
            sut.trigger()

    def test_react_weakref(self) -> None:
        sut = ReactorController()
        reactor = self.assert_not_reactor_called()
        sut.react_weakref(reactor)
        del reactor
        gc.collect()
        sut.trigger()

    def test_shutdown_weakref(self) -> None:
        sut = ReactorController()
        with self.assert_reactor_called() as reactor:
            sut.react_weakref(reactor)
            sut.trigger()
            sut.shutdown_weakref(reactor)
            sut.trigger()

    def test_suspend(self) -> None:
        sut = ReactorController()
        with self.assert_not_reactor_called() as reactor:
            sut.react_weakref(reactor)
            with ReactorController.suspend():
                sut.trigger()


class InstanceReactorControllerTest(ReactiveTestCase):
    def test_getattr_with_reactive_attribute(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self):
                pass
        sut = _InstanceReactorController(Subject())
        self.assert_is_reactive(sut.getattr('subject'))

    def test_getattr_with_non_existent_reactive_attribute(self) -> None:
        @reactive
        class Subject:
            def subject(self):
                pass
        sut = _InstanceReactorController(Subject())
        with self.assertRaises(AttributeError):
            sut.getattr('subject')


class ReactiveFunctionTest(ReactiveTestCase):
    def test_without_reactors(self) -> None:
        @reactive
        def subject():
            subject.tracker.append(True)
        subject.tracker = []
        subject()
        self.assertEquals([True], subject.tracker)

    def test_with_reactor(self) -> None:
        @reactive
        def subject():
            raise AssertionError('This function should not have been called.')

        with self.assert_reactor_called(subject):
            subject.react.trigger()

    def test_with_reactor_and_dependency(self) -> None:
        @reactive
        def dependency():
            pass

        @reactive
        def subject():
            if not subject.called:
                subject.called = True
                dependency()
        subject.called = False
        with self.assert_reactor_called(subject):
            # Call the reactive for the first time. This should result in dependency() being autowired.
            subject()
            # dependency() being autowired should cause the reactor to be called.
            dependency.react.trigger()

            # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
            subject()
            # dependency() no longer being autowired should not cause the reactor to be called.
            dependency.react.trigger()

    def test_on_trigger_call(self):
        @reactive(on_trigger_call=True)
        def subject():
            subject.tracker.append(True)
        subject.tracker = []
        subject.react.trigger()
        self.assertEquals([True], subject.tracker)

    def test_on_trigger_call_as_instance_method(self):
        @reactive
        class Subject:
            def __init__(self):
                self.tracker = []

            @reactive(on_trigger_call=True)
            def subject(self):
                self.tracker.append(True)
        subject = Subject()
        subject.react.getattr('subject').react.trigger()
        self.assertEquals([True], subject.tracker)


class ReactiveInstanceTest(ReactiveTestCase):
    def test_instance_trigger_without_reactors(self) -> None:
        @reactive
        class Subject:
            pass
        Subject().react.trigger()

    def test_instance_trigger_with_instance_reactor(self) -> None:
        @reactive
        class Subject:
            pass
        subject = Subject()
        with self.assert_reactor_called(subject):
            subject.react.trigger()

    def test_instance_trigger_with_instance_attribute_reactor(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with self.assert_not_reactor_called(subject.react.getattr('subject')):
            Subject().react.trigger()

    def test_instance_attribute_trigger_without_reactors(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self) -> None:
                pass
        Subject().react.getattr('subject').react.trigger()

    def test_instance_attribute_trigger_with_instance_reactor(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with self.assert_reactor_called(subject):
            subject.react.getattr('subject').react.trigger()

    def test_instance_attribute_trigger_with_instance_attribute_reactor(self) -> None:
        @reactive
        class Subject:
            @reactive
            def subject(self) -> None:
                pass
        subject = Subject()
        with self.assert_reactor_called(subject.react.getattr('subject')):
            subject.react.getattr('subject').react.trigger()


class ReactivePropertyTest(ReactiveTestCase):
    def test_without_fget(self) -> None:
        with self.assertRaises(UnsupportedReactive):
            reactive(property())

    def test_fget(self) -> None:
        @reactive
        def dependency():
            pass

        @reactive
        class Subject:
            def __init__(self):
                self._subject_called = False

            @reactive
            @property
            def subject(self):
                if not self._subject_called:
                    self._subject_called = True
                    return dependency()

            @reactive
            @property
            def subject2(self):
                if not self._subject_called:
                    self._subject_called = True
                    return dependency()

        subject = Subject()

        with self.assert_reactor_called(subject):
            with self.assert_in_scope(subject.react.getattr('subject')):
                # Call the reactive for the first time. This should result in dependency() being autowired.
                subject.subject

            # dependency() being autowired should cause the reactor to be called.
            dependency.react.trigger()

            # Call the reactive again. This should result in dependency() being ignored and not to be autowired again.
            with self.assert_in_scope(subject.react.getattr('subject')):
                subject.subject

        # dependency() no longer being autowired should not cause the reactor to be called.
        with self.assert_not_reactor_called(subject):
            dependency.react.trigger()

    def test_fset(self) -> None:
        @reactive
        class DependencyOne:
            pass

        @reactive
        class DependencyTwo:
            pass

        @reactive
        class Subject:
            def __init__(self):
                self._subject = 123

            @reactive
            @property
            def subject(self):
                return self._subject

            @subject.setter
            def subject(self, subject) -> None:
                self._subject = subject

        subject = Subject()
        dependency_one = DependencyOne()
        dependency_two = DependencyTwo()

        # Setting dependency_one should cause the reactor to be called.
        with self.assert_reactor_called(subject.react.getattr('subject')):
            subject.subject = dependency_one
            self.assertEquals(dependency_one, subject._subject)

        # dependency_one being autowired should cause the reactor to be called.
        with self.assert_reactor_called(subject.react.getattr('subject')):
            dependency_one.react.trigger()

        # Setting dependency_two should cause the reactor to be called.
        with self.assert_reactor_called(subject.react.getattr('subject')):
            subject.subject = dependency_two
            self.assertEquals(dependency_two, subject._subject)

        # dependency_one no longer being autowired should not cause the reactor to be called.
        with self.assert_not_reactor_called(subject.react.getattr('subject')):
            dependency_one.react.trigger()

    def test_fdel(self) -> None:
        @reactive
        class Dependency:
            pass

        @reactive
        class Subject:
            def __init__(self):
                self._subject = 123

            @reactive
            @property
            def subject(self):
                return self._subject

            @subject.setter
            def subject(self, subject) -> None:
                self._subject = subject

            @subject.deleter
            def subject(self) -> None:
                self._subject = None

        subject = Subject()

        # Even if the property's setter and getter weren't called, deletion should cause the reactor to be called.
        with self.assert_reactor_called(subject.react.getattr('subject')):
            del subject.subject
        self.assertIsNone(subject._subject)

        dependency = Dependency()

        # Setting dependency will autowire it.
        subject.subject = dependency

        # dependency_one no longer being autowired should not cause the reactor to be called.
        del subject.subject
        subject.react.getattr('subject').react.react_weakref(self.assert_not_reactor_called())
        dependency.react.trigger()

    def test_on_trigger(self) -> None:
        @reactive
        class Subject:
            def __init__(self):
                self._subject = 123

            @reactive(on_trigger=(lambda instance: setattr(instance, '_subject', None),))
            @property
            def subject(self):
                return self._subject

        subject = Subject()
        subject.react.getattr('subject').react.trigger()
        self.assertIsNone(subject._subject)


class ReactiveDictTest(ReactiveTestCase):
    @reactive
    class Reactive:
        pass

    def test_clear(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(one=1, reactive=reactive_value)
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.clear()
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_get(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertEquals(2, sut.get('two'))

    def test_items(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertEquals([('one', 1), ('two', 2)], list(sut.items()))

    def test_keys(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertEquals(['one', 'two'], list(sut.keys()))

    def test_pop(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.pop('reactive')
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_popitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                key, value = sut.popitem()
        self.assertEquals('reactive', key)
        self.assertEquals(reactive_value, value)
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_setdefault_with_existing_key(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(reactive='notActuallyReactive')
        with self.assert_in_scope(sut):
            with self.assert_not_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        self.assertNotEquals(reactive_value, dict.get(sut, 'reactive'))
        self.assertNotIn(sut, reactive_value.react._reactors)

    def test_setdefault_with_unknown_key(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict()
        with self.assert_in_scope(sut):
            with self.assert_reactor_called(sut):
                sut.setdefault('reactive', reactive_value)
        self.assertEquals(reactive_value, dict.get(sut, 'reactive'))
        self.assertIn(sut, reactive_value.react._reactors)

    def test_update(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(one=1)
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.update({
                    'reactive': reactive_value
                })
        self.assertEquals(reactive_value, dict.get(sut, 'reactive'))
        self.assertIn(sut, reactive_value.react._reactors)

    def test_values(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertCountEqual([1, 2], list(sut.values()))

    def test_contains(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertIn('one', sut)
            self.assertNotIn('three', sut)

    def test_delitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict(reactive=reactive_value)
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                del sut['reactive']
        self.assertCountEqual([], sut)
        self.assertCountEqual([], reactive_value.react._reactors)

    def test_eq(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertEquals({
                'one': 1,
                'two': 2,
            }, sut)

    def test_getitem(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertEquals(2, sut['two'])

    def test_iter(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertCountEqual(['one', 'two'], iter(sut))

    def test_len(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertEquals(2, len(sut))

    def test_ne(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            self.assertNotEquals({
                'two': 1,
                'one': 2,
            }, sut)

    @unittest.skipIf(not hasattr(dict, '__reversed__'), 'Dictionary reversal is available in Python 3.8 and later only.')
    def test_reversed(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            # Because dictionary order isn't guaranteed before Python 3.7, we cannot compare to a hardcoded list of
            # expected keys.
            self.assertEquals(['two', 'one'], list(reversed(sut)))

    def test_setitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveDict()
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut['reactive'] = reactive_value
        self.assertEquals(reactive_value, sut['reactive'])
        with self.assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_sizeof(self) -> None:
        sut = ReactiveDict(one=1, two=2)
        with self.assert_in_scope(sut):
            sys.getsizeof(sut)


class ReactiveListTest(ReactiveTestCase):
    @reactive
    class Reactive:
        pass

    def test_append(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList()
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.append(reactive_value)
        with self.assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_clear(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList(reactive=reactive_value)
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.clear()
        self.assertEquals([], sut)
        self.assertEquals([], reactive_value.react._reactors)

    def test_copy(self) -> None:
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            self.assertEquals([1, 2], sut.copy())

    def test_count(self) -> None:
        sut = ReactiveList([1, 2, 1])
        with self.assert_in_scope(sut):
            self.assertEquals(2, sut.count(1))

    def test_extend(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([1, 2])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.extend([reactive_value1, reactive_value2])
        self.assertEquals([1, 2, reactive_value1, reactive_value2], sut)
        with self.assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with self.assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_index_without_slice(self) -> None:
        sut = ReactiveList([1, 2, 1, 2, 1, 2, 1, 2])
        with self.assert_in_scope(sut):
            self.assertEquals(1, sut.index(2))

    def test_index_with_slice(self) -> None:
        sut = ReactiveList([1, 2, 1, 2, 1, 2, 1, 2])
        with self.assert_in_scope(sut):
            self.assertEquals(2, sut.index(1, 2, 5))

    def test_insert(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([1, 2])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.insert(1, reactive_value)
        self.assertEquals([1, reactive_value, 2], sut)
        with self.assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_without_index(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([1, 2, reactive_value])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.pop()
        self.assertEquals([1, 2], sut)
        with self.assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_pop_with_index(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([1, reactive_value, 2])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.pop(1)
        self.assertEquals([1, 2], sut)
        with self.assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_remove(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([reactive_value])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.remove(reactive_value)
        self.assertEquals([], sut)
        with self.assert_not_reactor_called(sut):
            reactive_value.react.trigger()

    def test_reverse(self) -> None:
        sut = ReactiveList([1, 2, 3])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.reverse()
        self.assertEquals([3, 2, 1], sut)

    def test_sort(self) -> None:
        sut = ReactiveList([3, 2, 1])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.sort()
        self.assertEquals([1, 2, 3], sut)

    def test_sort_with_key(self) -> None:
        sut = ReactiveList(['xc', 'yb', 'za'])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.sort(key=lambda x: x[1])
        self.assertEquals(['za', 'yb', 'xc'], sut)

    def test_sort_with_reversed(self) -> None:
        sut = ReactiveList([1, 2, 3])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut.sort(reverse=True)
        self.assertEquals([3, 2, 1], sut)

    def test_add(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([reactive_value])
        other = [1, 2]
        with self.assert_scope_empty():
            with self.assert_not_reactor_called(sut):
                new_sut = sut + other
        self.assertEquals([reactive_value, 1, 2], new_sut)
        with self.assert_reactor_called(new_sut):
            reactive_value.react.trigger()

    def test_contains(self) -> None:
        sut = ReactiveList([1])
        with self.assert_in_scope(sut):
            self.assertIn(1, sut)
            self.assertNotIn(2, sut)

    def test_delitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([reactive_value])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                del sut[0]
        self.assertEquals([], sut)
        self.assertEquals([], reactive_value.react._reactors)

    def test_eq(self) -> None:
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            self.assertEquals([1, 2], sut)

    def test_getitem(self) -> None:
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            self.assertEquals(2, sut[1])

    def test_iadd(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            with self.assert_reactor_called(sut):
                sut += [reactive_value1, reactive_value2]
        self.assertEquals([1, 2, reactive_value1, reactive_value2], sut)
        with self.assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with self.assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_imul(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with self.assert_in_scope(sut):
            with self.assert_reactor_called(sut):
                sut *= 2
        self.assertEquals([reactive_value1, reactive_value2, reactive_value1, reactive_value2], sut)
        with self.assert_reactor_called(sut):
            reactive_value1.react.trigger()
        with self.assert_reactor_called(sut):
            reactive_value2.react.trigger()

    def test_iter(self) -> None:
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            self.assertEquals([1, 2], list(iter(sut)))

    def test_len(self) -> None:
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            self.assertEquals(2, len(sut))

    def test_mul(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with self.assert_scope_empty():
            with self.assert_not_reactor_called(sut):
                new_sut = sut * 2
        self.assertEquals([reactive_value1, reactive_value2, reactive_value1, reactive_value2], new_sut)
        with self.assert_reactor_called(new_sut):
            reactive_value1.react.trigger()
        with self.assert_reactor_called(new_sut):
            reactive_value2.react.trigger()

    def test_ne(self) -> None:
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            self.assertNotEquals([2, 1], sut)

    def test_reversed(self) -> None:
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            self.assertEquals([2, 1], list(reversed(sut)))

    def test_rmul(self) -> None:
        reactive_value1 = self.Reactive()
        reactive_value2 = self.Reactive()
        sut = ReactiveList([reactive_value1, reactive_value2])
        with self.assert_scope_empty():
            with self.assert_not_reactor_called(sut):
                new_sut = 2 * sut
        self.assertEquals([reactive_value1, reactive_value2, reactive_value1, reactive_value2], new_sut)
        with self.assert_reactor_called(new_sut):
            reactive_value1.react.trigger()
        with self.assert_reactor_called(new_sut):
            reactive_value2.react.trigger()

    def test_setitem(self) -> None:
        reactive_value = self.Reactive()
        sut = ReactiveList([1, 2])
        with self.assert_scope_empty():
            with self.assert_reactor_called(sut):
                sut[1] = reactive_value
        self.assertEquals(reactive_value, sut[1])
        with self.assert_reactor_called(sut):
            reactive_value.react.trigger()

    def test_sizeof(self) -> None:
        sut = ReactiveList([1, 2])
        with self.assert_in_scope(sut):
            sys.getsizeof(sut)
