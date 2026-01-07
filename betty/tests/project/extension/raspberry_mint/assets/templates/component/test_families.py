from betty.ancestry.person import Person
from betty.privacy import Privacy
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.test_utils.jinja2 import assert_template_file


async def test_minimal() -> None:
    person = Person()
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert not actual


async def test_with_parents() -> None:
    parent = Person(id="P0")
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert parent.public_id in actual


async def test_with_private_parents() -> None:
    parent = Person(id="P0", privacy=Privacy.PRIVATE)
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert parent.id not in actual


async def test_with_siblings() -> None:
    parent = Person(id="P0")
    sibling = Person(id="P1", parents=[parent])
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert sibling.public_id in actual


async def test_with_private_siblings() -> None:
    parent = Person(id="P0")
    sibling = Person(id="P1", parents=[parent], privacy=Privacy.PRIVATE)
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert sibling.id not in actual


async def test_with_children() -> None:
    child = Person(id="P0")
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert child.public_id in actual


async def test_with_private_children() -> None:
    child = Person(id="P0", privacy=Privacy.PRIVATE)
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert child.id not in actual


async def test_with_co_parents() -> None:
    child = Person()
    co_parent = Person(id="P0", children=[child])
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert co_parent.public_id in actual


async def test_with_private_co_parents() -> None:
    child = Person()
    co_parent = Person(id="P0", children=[child], privacy=Privacy.PRIVATE)
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
        },
        extensions={RaspberryMint},
        template="component/families.html.j2",
    ) as (actual, _):
        assert co_parent.id not in actual
