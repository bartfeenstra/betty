from betty.asset_directories.raspberry_mint import RASPBERRY_MINT
from betty.entities.person import Person
from betty.extensions._theme import person_descendant_families
from betty.privacy import Privacy
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    person = Person()
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert not actual


async def test_with_parents(assert_template_file: AssertTemplateFile) -> None:
    parent = Person(id="P0")
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert parent.public_id in actual


async def test_with_private_parents(assert_template_file: AssertTemplateFile) -> None:
    parent = Person(id="P0", privacy=Privacy.PRIVATE)
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert parent.id not in actual


async def test_with_siblings(assert_template_file: AssertTemplateFile) -> None:
    parent = Person(id="P0")
    sibling = Person(id="P1", parents=[parent])
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert sibling.public_id in actual


async def test_with_private_siblings(assert_template_file: AssertTemplateFile) -> None:
    parent = Person(id="P0")
    sibling = Person(id="P1", parents=[parent], privacy=Privacy.PRIVATE)
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert sibling.id not in actual


async def test_with_children(assert_template_file: AssertTemplateFile) -> None:
    child = Person(id="P0")
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
            "person_descendant_families": person_descendant_families(person),
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert child.public_id in actual


async def test_with_private_children(assert_template_file: AssertTemplateFile) -> None:
    child = Person(id="P0", privacy=Privacy.PRIVATE)
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert child.id not in actual


async def test_with_co_parents(assert_template_file: AssertTemplateFile) -> None:
    child = Person()
    co_parent = Person(id="P0", children=[child])
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
            "person_descendant_families": person_descendant_families(person),
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert co_parent.public_id in actual


async def test_with_private_co_parents(
    assert_template_file: AssertTemplateFile,
) -> None:
    child = Person()
    co_parent = Person(id="P0", children=[child], privacy=Privacy.PRIVATE)
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={RASPBERRY_MINT},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert co_parent.id not in actual
