class Betty:
    def __init__(self, betty_root_path: str, output_directory_path: str):
        self._betty_root_path = betty_root_path
        self._output_directory_path = output_directory_path

    @property
    def betty_root_path(self):
        return self._betty_root_path

    @property
    def output_directory_path(self):
        return self._output_directory_path
