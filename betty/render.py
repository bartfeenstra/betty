from typing import Optional, Dict, Any, Sequence

RenderArguments = Optional[Dict[str, Any]]


class Renderer:
    async def render_tree(self, render_path: str, file_arguments: RenderArguments = None) -> None:
        raise NotImplementedError


class SequentialRenderer(Renderer):
    def __init__(self, renderers: Sequence[Renderer]):
        self._renderers = renderers

    async def render_tree(self, render_path: str, file_arguments: RenderArguments = None) -> None:
        for renderer in self._renderers:
            await renderer.render_tree(render_path, file_arguments)
