import os
from glob import glob

import sass


def render_tree(path: str) -> None:
    sass.compile(dirname=(path, path), output_style='compressed')
    for extension in ['sass', 'scss']:
        patterns = [
            # Files in the path.
            os.path.join(path, '*.' + extension),
            # Files in the path's subdirectories.
            os.path.join(path, '**', '*.' + extension),
        ]
        for pattern in patterns:
            for filepath in glob(pattern):
                os.remove(filepath)
