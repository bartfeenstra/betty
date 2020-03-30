from typing import List


class Renderer:
    async def render_file(self, file_path: str) -> None:
        raise NotImplementedError

    async def render_tree(self, tree_path: str) -> None:
        raise NotImplementedError


class SequentialRenderer(Renderer):
    def __init__(self, renderers: List[Renderer]):
        self._renderers = renderers

    async def render_file(self, file_path: str) -> None:
        for renderer in self._renderers:
            await renderer.render_file(file_path)

    async def render_tree(self, tree_path: str) -> None:
        for renderer in self._renderers:
            await renderer.render_tree(tree_path)
