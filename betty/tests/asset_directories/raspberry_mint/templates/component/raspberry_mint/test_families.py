from betty.asset_directories.raspberry_mint import raspberry_mint
from betty.entities.person import Person
from betty.privacy import Privacy
from betty.service_providers._theme import person_descendant_families
from betty.test_utils.conftest import AssertTemplateFile


async def test_minimal(assert_template_file: AssertTemplateFile) -> None:
    person = Person()
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert not actual


async def test_with_parents(assert_template_file: AssertTemplateFile) -> None:
    parent = Person(id="my-first-person")
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert parent.id in actual


async def test_with_private_parents(assert_template_file: AssertTemplateFile) -> None:
    parent = Person(id="my-first-person", privacy=Privacy.PRIVATE)
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert parent.id not in actual


async def test_with_siblings(assert_template_file: AssertTemplateFile) -> None:
    parent = Person(id="my-first-person")
    sibling = Person(id="my-second-person", parents=[parent])
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert sibling.id in actual


async def test_with_private_siblings(assert_template_file: AssertTemplateFile) -> None:
    parent = Person(id="my-first-person")
    sibling = Person(id="my-second-person", parents=[parent], privacy=Privacy.PRIVATE)
    person = Person(parents=[parent])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert sibling.id not in actual


async def test_with_children(assert_template_file: AssertTemplateFile) -> None:
    child = Person(id="my-first-person")
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
            "person_descendant_families": person_descendant_families(person),
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert child.id in actual


async def test_with_private_children(assert_template_file: AssertTemplateFile) -> None:
    child = Person(id="my-first-person", privacy=Privacy.PRIVATE)
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert child.id not in actual


async def test_with_co_parents(assert_template_file: AssertTemplateFile) -> None:
    child = Person()
    co_parent = Person(id="my-first-person", children=[child])
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
            "person_descendant_families": person_descendant_families(person),
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert co_parent.id in actual


async def test_with_private_co_parents(
    assert_template_file: AssertTemplateFile,
) -> None:
    child = Person()
    co_parent = Person(id="my-first-person", children=[child], privacy=Privacy.PRIVATE)
    person = Person(children=[child])
    async with assert_template_file(
        data={
            "person": person,
        },
        assets={raspberry_mint},
        template="component/raspberry-mint/families.html.j2",
    ) as (actual, _):
        assert co_parent.id not in actual
