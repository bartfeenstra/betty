from os import path


def rootname(source_path: str) -> str:
    root = source_path
    while True:
        possible_root = path.dirname(root)
        if possible_root == root:
            return root
        root = possible_root
