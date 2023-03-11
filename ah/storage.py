import os
from gzip import GzipFile

from ah.fs import ensure_path, remove_file


class BaseFile:
    def __init__(self, file_path: str) -> None:
        file_path = os.path.normcase(file_path)
        file_name = os.path.basename(file_path)
        base_path = os.path.dirname(file_path)
        if base_path:
            ensure_path(base_path)
        self.file_path = file_path
        self.file_name = file_name

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        return f'{cls_name}("{self.file_path}")'

    def exists(self):
        return os.path.exists(self.file_path)

    def remove(self):
        remove_file(self.file_path)

    def open(self, mode="rb"):
        raise NotImplementedError


class TextFile(BaseFile):
    def __init__(self, file_path: str) -> None:
        super().__init__(file_path)

    def open(self, mode="r", **kwargs):
        return open(self.file_path, mode, **kwargs)


class BinaryFile(BaseFile):
    def __init__(self, file_path: str, use_compression=False) -> None:
        super().__init__(file_path)
        self.use_compression = use_compression

    # def _get_path(self, name, use_compression: bool = False):
    #     file_name = f"{name}.bin.gz" if use_compression else f"{name}.bin"
    #     return os.path.join(self.base_path, file_name)

    def open(self, mode="rb"):
        if self.use_compression:
            return GzipFile(self.file_path, mode)

        else:
            return open(self.file_path, mode)
