from os import path
from typing import Optional, Dict, Any, Sequence, Callable, Tuple, Awaitable, List

from betty.fs import iterfiles, makedirs

_Pipeline = Sequence[Callable]
_PipelineKwargs = Dict
_Pipe = Callable[[_PipelineKwargs], Awaitable[_PipelineKwargs]]
TemplateArguments = Optional[Dict[str, Any]]


class SequentialRenderDirectoryTo:
    def __init__(self, renderers: Sequence['Renderer'], source_directory_path: str):
        self._renderers = renderers
        self._source_directory_path = source_directory_path
        self._pipelines = []
        self._initialized = False

    async def __call__(self, destination_directory_path: str, template_arguments: TemplateArguments = None) -> None:
        await self._build_pipelines()
        for pipeline, initial_pipeline_kwargs in self._pipelines:
            pipeline_kwargs = initial_pipeline_kwargs.copy()
            pipeline_kwargs['destination_directory_path'] = destination_directory_path
            await self._execute_pipeline(pipeline, pipeline_kwargs, template_arguments)

    async def _execute_pipeline(self, pipeline, pipeline_kwargs, template_arguments: TemplateArguments) -> None:
        pipeline_kwargs['template_arguments'] = template_arguments
        for pipe in pipeline:
            pipeline_kwargs = await pipe(pipeline_kwargs)

    async def _build_pipelines(self):
        if self._initialized:
            return
        self._initialized = True

        for file_path in iterfiles(self._source_directory_path):
            self._pipelines.append(await self._build_pipeline(file_path, self._collect_renderers(file_path)))

    def _collect_renderers(self, file_path: str) -> List['Renderer']:
        for renderer in self._renderers:
            if renderer.consumes_file_path(file_path):
                return [renderer] + self._collect_renderers(renderer.update_file_path(file_path))
        return []

    async def _build_pipeline(self, file_path: str, renderers: Sequence['Renderer']) -> Tuple[_Pipeline, _PipelineKwargs]:
        initial_pipeline_kwargs = {
            'file_path': file_path,
            'destination_directory_path': None,
            'template': None,
            'bytes': None,
            'template_arguments': {},
        }
        if renderers:
            initial_pipeline_kwargs = await self._render_file_to_string()(initial_pipeline_kwargs)
            pipeline = []
            for renderer in renderers:
                pipeline.append(self._render_string(renderer))
            pipeline.append(self._render_string_to_file())
        else:
            initial_pipeline_kwargs = await self._render_file_to_bytes()(initial_pipeline_kwargs)
            pipeline = [lambda pipeline_kwargs: self._render_bytes_to_file()]

        return pipeline, initial_pipeline_kwargs

    def _render_string(self, renderer: 'Renderer') -> _Pipe:
        async def _render(pipeline_kwargs: _PipelineKwargs) -> _PipelineKwargs:
            pipeline_kwargs['file_path'] = renderer.update_file_path(pipeline_kwargs['file_path'])
            pipeline_kwargs['template'] = await renderer.render_string(template=pipeline_kwargs['template'], template_arguments=pipeline_kwargs['template_arguments'])
            return pipeline_kwargs
        return _render

    def _render_file_to_string(self) -> _Pipe:
        async def _render(pipeline_kwargs: _PipelineKwargs) -> _PipelineKwargs:
            with open(pipeline_kwargs['file_path']) as f:
                pipeline_kwargs['template'] = f.read()
            return pipeline_kwargs
        return _render

    def _render_string_to_file(self) -> _Pipe:
        async def _render(pipeline_kwargs: _PipelineKwargs) -> _PipelineKwargs:
            destination_file_path = path.join(pipeline_kwargs['destination_directory_path'], path.relpath(pipeline_kwargs['file_path'], self._source_directory_path))
            makedirs(path.dirname(destination_file_path))
            with open(destination_file_path, 'w') as f:
                f.write(pipeline_kwargs['template'])
            return pipeline_kwargs
        return _render

    def _render_file_to_bytes(self) -> _Pipe:
        async def _render(pipeline_kwargs: _PipelineKwargs) -> _PipelineKwargs:
            with open(pipeline_kwargs['file_path'], 'rb') as f:
                pipeline_kwargs['bytes'] = f.read()
            return pipeline_kwargs
        return _render

    def _render_bytes_to_file(self) -> _Pipe:
        async def _render(pipeline_kwargs: _PipelineKwargs) -> _PipelineKwargs:
            destination_file_path = path.join(pipeline_kwargs['destination_directory_path'], path.relpath(pipeline_kwargs['file_path'], self._source_directory_path))
            makedirs(path.dirname(destination_file_path))
            with open(destination_file_path, 'wb') as f:
                f.write(pipeline_kwargs['bytes'])
            return pipeline_kwargs
        return _render


class Renderer:
    async def render_string(self, template: str, template_arguments: TemplateArguments = None) -> str:
        raise NotImplementedError

    def consumes_file_path(self, file_path: str) -> bool:
        raise NotImplementedError

    def update_file_path(self, file_path: str) -> str:
        """
        Update a file path as if it has been rendered by this renderer.
        """
        raise NotImplementedError

    async def render_file(self, file_path: str, template_arguments: TemplateArguments = None) -> None:
        raise NotImplementedError

    async def render_directory(self, directory_path: str, template_arguments: TemplateArguments = None) -> None:
        raise NotImplementedError

    async def render_directory_to(self, directory_path: str) -> SequentialRenderDirectoryTo:
        return SequentialRenderDirectoryTo([self], directory_path)


class SequentialRenderer(Renderer):
    def __init__(self, renderers: Sequence[Renderer]):
        self._renderers = renderers

    def consumes_file_path(self, file_path: str) -> bool:
        return True

    def update_file_path(self, file_path: str) -> str:
        for renderer in self._renderers:
            if renderer.consumes_file_path(file_path):
                file_path = renderer.update_file_path(file_path)
        return file_path

    async def render_file(self, file_path: str, template_arguments: TemplateArguments = None) -> None:
        for renderer in self._renderers:
            await renderer.render_file(file_path, template_arguments)

    async def render_directory(self, directory_path: str, template_arguments: TemplateArguments = None) -> None:
        for renderer in self._renderers:
            await renderer.render_directory(directory_path, template_arguments)

    async def render_directory_to(self, directory_path: str) -> SequentialRenderDirectoryTo:
        return SequentialRenderDirectoryTo(self._renderers, directory_path)
