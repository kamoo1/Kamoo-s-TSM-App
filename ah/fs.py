import os


def get_temp_path() -> str:
    # windows %TEMP%, linux-like /tmp
    if os.name == "nt":
        return os.environ.get("TEMP")

    else:
        return "/tmp"


def ensure_path(path):
    # if not os.path.exists(path):
    #     os.makedirs(path)

    # make dirs recursively
    os.makedirs(path, exist_ok=True)


def remove_path(path, parent=False):
    if os.path.exists(path):
        for file in os.listdir(path):
            os.remove(os.path.join(path, file))

        if parent:
            os.rmdir(path)


def remove_file(path):
    # exists as file
    if os.path.isfile(path):
        os.remove(path)
