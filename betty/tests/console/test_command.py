from betty.console.command import CommandDefinition


class TestCommandDefinition:
    def test_aliases(self) -> None:
        alias = "hello-world"
        sut = CommandDefinition("-", label="-", aliases=[alias])
        assert list(sut.aliases) == [alias]
