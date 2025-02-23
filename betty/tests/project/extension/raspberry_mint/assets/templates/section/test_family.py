from betty.ancestry.person import Person
from betty.project.extension.raspberry_mint import RaspberryMint
from betty.project.extension.trees import Trees
from betty.test_utils.jinja2 import TemplateFileTestBase


class Test(TemplateFileTestBase):
    extensions = {RaspberryMint, Trees}
    template = "section/family.html.j2"

    async def test_minimal(self) -> None:
        person = Person()
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert not actual

    async def test_with_parents(self) -> None:
        parent = Person(id="P0")
        person = Person(parents=[parent])
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert parent.id in actual

    async def test_with_private_parents(self) -> None:
        parent = Person(id="P0", private=True)
        person = Person(parents=[parent])
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert parent.id not in actual

    async def test_with_siblings(self) -> None:
        parent = Person(id="P0")
        sibling = Person(id="P1", parents=[parent])
        person = Person(parents=[parent])
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert sibling.id in actual

    async def test_with_private_siblings(self) -> None:
        parent = Person(id="P0")
        sibling = Person(id="P1", parents=[parent], private=True)
        person = Person(parents=[parent])
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert sibling.id not in actual

    async def test_with_children(self) -> None:
        child = Person(id="P0")
        person = Person(children=[child])
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert child.id in actual

    async def test_with_private_children(self) -> None:
        child = Person(id="P0", private=True)
        person = Person(children=[child])
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert child.id not in actual

    async def test_with_co_parents(self) -> None:
        child = Person()
        co_parent = Person(id="P0", children=[child])
        person = Person(children=[child])
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert co_parent.id in actual

    async def test_with_private_co_parents(self) -> None:
        child = Person()
        co_parent = Person(id="P0", children=[child], private=True)
        person = Person(children=[child])
        async with self.assert_template_file(
            data={
                "entity": person,
                "page_resource": "betty:///index.html",
            }
        ) as (actual, _):
            assert co_parent.id not in actual
