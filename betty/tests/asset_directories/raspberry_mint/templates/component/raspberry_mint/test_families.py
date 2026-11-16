from betty.entities.person import Person
from betty.privacy import Privacy
from betty.service_providers._theme import person_descendant_families
from betty.test_utils.conftest import AssertJinja


async def test_minimal(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    person = Person()
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2", data={"person": person}
    ) as rendered:
        assert not rendered


async def test_with_parents(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    parent = Person(id="my-first-person")
    person = Person(parents=[parent])
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2", data={"person": person}
    ) as rendered:
        assert parent.id in rendered


async def test_with_private_parents(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    parent = Person(id="my-first-person", privacy=Privacy.PRIVATE)
    person = Person(parents=[parent])
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2", data={"person": person}
    ) as rendered:
        assert parent.id not in rendered


async def test_with_siblings(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    parent = Person(id="my-first-person")
    sibling = Person(id="my-second-person", parents=[parent])
    person = Person(parents=[parent])
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2", data={"person": person}
    ) as rendered:
        assert sibling.id in rendered


async def test_with_private_siblings(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    parent = Person(id="my-first-person")
    sibling = Person(id="my-second-person", parents=[parent], privacy=Privacy.PRIVATE)
    person = Person(parents=[parent])
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2", data={"person": person}
    ) as rendered:
        assert sibling.id not in rendered


async def test_with_children(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    child = Person(id="my-first-person")
    person = Person(children=[child])
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2",
        data={
            "person": person,
            "person_descendant_families": person_descendant_families(person),
        },
    ) as rendered:
        assert child.id in rendered


async def test_with_private_children(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    child = Person(id="my-first-person", privacy=Privacy.PRIVATE)
    person = Person(children=[child])
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2", data={"person": person}
    ) as rendered:
        assert child.id not in rendered


async def test_with_co_parents(assert_raspberry_mint_jinja_file: AssertJinja) -> None:
    child = Person()
    co_parent = Person(id="my-first-person", children=[child])
    person = Person(children=[child])
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2",
        data={
            "person": person,
            "person_descendant_families": person_descendant_families(person),
        },
    ) as rendered:
        assert co_parent.id in rendered


async def test_with_private_co_parents(
    assert_raspberry_mint_jinja_file: AssertJinja,
) -> None:
    child = Person()
    co_parent = Person(id="my-first-person", children=[child], privacy=Privacy.PRIVATE)
    person = Person(children=[child])
    async with assert_raspberry_mint_jinja_file(
        "component/raspberry-mint/families.html.j2", data={"person": person}
    ) as rendered:
        assert co_parent.id not in rendered
