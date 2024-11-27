from betty.documentation import _prebuild_documentation
from betty.project.extension.webpack import build


async def prebuild() -> None:
    """
    Prebuild assets for inclusion in package builds.
    """
    await build.prebuild()
    await _prebuild_documentation()
