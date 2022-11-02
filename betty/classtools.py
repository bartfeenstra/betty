def repr_instance(instance: object, **attributes) -> str:
    return '<{}.{}{}>'.format(
        instance.__class__.__module__,
        instance.__class__.__name__,
        (' ' + ', '.join(map(lambda x: f'{x[0]}={x[1]}', attributes.items()))).rstrip(),
    )


class Repr:
    def __repr__(self):
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
