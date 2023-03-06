import os
import json
from gzip import GzipFile

from ah import config
from ah.fs import get_temp_path, ensure_path, remove_path, remove_file

# TODO: cache isn't using storage class, jsonstorage is orphaned


class JSONLStorage(object):
    def __init__(self) -> None:
        self._path = get_temp_path("{}.storage".format(config.APP_NAME))
        ensure_path(self._path)

    def get_file_path_of_table(self, name):
        return os.path.join(self._path, f"{name}.jsonl")

    def load_table(self, name):
        path = self.get_file_path_of_table(name)
        if not os.path.exists(path):
            return None

        with open(path, "r") as f:
            return json.load(f)

    def save_table(self, name, data):
        path = self.get_file_path_of_table(name)
        with open(path, "w") as f:
            json.dump(data, f)

    def purge(self):
        remove_path(self._path)


class BaseFile:
    def __init__(self, file_path: str) -> None:
        base_path = os.path.dirname(file_path)
        ensure_path(base_path)
        self.file_path = file_path

    def __repr__(self) -> str:
        cls_name = self.__class__.__name__
        return f'{cls_name}("{self.file_path}")'

    def exists(self):
        return os.path.exists(self.file_path)

    def remove(self):
        remove_file(self.file_path)


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
