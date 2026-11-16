from betty.classtools.store import StoreClassVar


class TestStoreClassVar:
    def test___set_name__(self) -> None:
        class _Owner:
            my_first_store = StoreClassVar()

        owner = _Owner()
        _Owner.my_first_store._store.set(owner, "Hello, world!")
        assert owner._betty_class_var_store__my_first_store == "Hello, world!"  # ty: ignore[unresolved-attribute]
