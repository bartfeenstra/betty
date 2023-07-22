from typing import Any


def repr_instance(instance: object, **attributes: Any) -> str:
    return '<{}.{} object at {}; {}>'.format(
        instance.__class__.__module__,
        instance.__class__.__name__,
        hex(id(instance)),
        (' ' + ', '.join(map(lambda x: f'{x[0]}={x[1]}', attributes.items()))).rstrip(),
    )


class Repr:
    def __repr__(self) -> str:
        attribute_names = [
            *self.__dict__.keys(),
            *getattr(self, '__slots__', []),
        ]

        return repr_instance(
            self,
            **{
                attribute_name: getattr(self, attribute_name)
                for attribute_name
                in attribute_names
            },
        )
