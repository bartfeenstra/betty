from typing import List, Optional, Dict, Any

FileArguments = Optional[Dict[str, Any]]


class Renderer:
    async def render_file(self, file_path: str, file_arguments: FileArguments = None) -> None:
        raise NotImplementedError

    async def render_tree(self, tree_path: str, file_arguments: FileArguments = None) -> None:
        raise NotImplementedError


class SequentialRenderer(Renderer):
    def __init__(self, renderers: List[Renderer]):
        self._renderers = renderers

    async def render_file(self, file_path: str, file_arguments: FileArguments = None) -> None:
        for renderer in self._renderers:
            await renderer.render_file(file_path, file_arguments)

    async def render_tree(self, tree_path: str, file_arguments: FileArguments = None) -> None:
        for renderer in self._renderers:
            await renderer.render_tree(tree_path, file_arguments)
