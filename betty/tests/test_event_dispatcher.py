from collections.abc import Mapping, Sequence, MutableSequence

from betty.event_dispatcher import (
    EventDispatcher,
    Event,
    EventHandlerRegistry,
    EventHandler,
)


def _assert_handlers(
    expected: Mapping[
        type[Event], MutableSequence[MutableSequence[EventHandler[Event]]]
    ],
    actual: Mapping[type[Event], Sequence[Sequence[EventHandler[Event]]]],
) -> None:
    assert {
        event_type: [list(event_type_batch) for event_type_batch in event_type_batches]
        for event_type, event_type_batches in actual.items()
    } == expected


async def _any_handler_one(dispatched_event: Event) -> None:
    pass


async def _any_handler_two(dispatched_event: Event) -> None:
    pass


async def _any_handler_three(dispatched_event: Event) -> None:
    pass


async def _any_handler_four(dispatched_event: Event) -> None:
    pass


class TestEventHandlerRegistry:
    async def test_add_handler_with_single_handler(self) -> None:
        sut = EventHandlerRegistry()
        sut.add_handler(EventDispatcherTestEvent, _any_handler_one)
        _assert_handlers({EventDispatcherTestEvent: [[_any_handler_one]]}, sut.handlers)

    async def test_add_handler_with_batch(self) -> None:
        sut = EventHandlerRegistry()
        sut.add_handler(
            EventDispatcherTestEvent,
            _any_handler_one,
            _any_handler_two,
            _any_handler_three,
        )
        _assert_handlers(
            {
                EventDispatcherTestEvent: [
                    [_any_handler_one, _any_handler_two, _any_handler_three]
                ]
            },
            sut.handlers,
        )

    async def test_add_registry(self) -> None:
        sut = EventHandlerRegistry()

        registry = EventHandlerRegistry()
        registry.add_handler(EventDispatcherTestEvent, _any_handler_one)
        registry.add_handler(
            EventDispatcherTestEvent, _any_handler_two, _any_handler_three
        )
        registry.add_handler(EventDispatcherTestEvent, _any_handler_four)
        sut.add_registry(registry)
        _assert_handlers(
            {
                EventDispatcherTestEvent: [
                    [_any_handler_one],
                    [_any_handler_two, _any_handler_three],
                    [_any_handler_four],
                ]
            },
            sut.handlers,
        )


class EventDispatcherTestEvent(Event):
    def __init__(self):
        self.check = False


class TestEventDispatcher:
    async def test_dispatch(self) -> None:
        async def _handler(dispatched_event: EventDispatcherTestEvent) -> None:
            dispatched_event.check = True

        sut = EventDispatcher()
        sut.add_handler(EventDispatcherTestEvent, _handler)
        event = EventDispatcherTestEvent()
        await sut.dispatch(event)
        assert event.check
