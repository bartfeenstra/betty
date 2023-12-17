from typing import Any, TypeAlias

DictState: TypeAlias = dict[str, Any]

SlotsState: TypeAlias = dict[str, Any]

State: TypeAlias = tuple[DictState, SlotsState]


class Pickleable:
    def __getstate__(self) -> State:
        return {}, {}

    def __setstate__(self, state: State):
        dict_state, slots_state = state
        self.__dict__.update(**dict_state)
        for slot_name, slot_value in slots_state.items():
            setattr(self, slot_name, slot_value)
