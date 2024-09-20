from betty.documentation import _prebuild_documentation
from betty.project.extension.webpack import _prebuild_webpack_assets


async def prebuild() -> None:
    """
    Prebuild assets for inclusion in package builds.
    """
    await _prebuild_webpack_assets()
    await _prebuild_documentation()
