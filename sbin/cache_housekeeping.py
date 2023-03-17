import os
import re
import argparse

from ah.models import (
    DBFileName,
    DBType,
    DBTypeEnum,
    DBExtEnum,
    Namespace,
    RegionEnum,
    GameVersionEnum,
    NameSpaceCategoriesEnum,
)

curr_db_data_matcher = re.compile(
    r"^(?P<region>tw)-(?P<db_type>\d+-auctions|commodities)\.(?P<ext>gz|bin)$"
)


def move(src, dst):
    print(f"Moving {src} to {dst}")
    pass


def rename_db_files(db_path: str):
    name_space = Namespace(
        category=NameSpaceCategoriesEnum.DYNAMIC,
        region=RegionEnum.TW,
        game_version=GameVersionEnum.RETAIL,
    )

    curr_fns = list(os.listdir(db_path))
    print(f"Current files: {curr_fns}")

    # list all file names under `db_path`
    for curr_fn in curr_fns:
        # match `DB_FILE_MATCHER`
        m = curr_db_data_matcher.match(curr_fn)
        if m:
            _ = m.group("region")
            db_type_str = m.group("db_type")
            if db_type_str.endswith(DBTypeEnum.AUCTIONS):
                db_type = DBType.from_str(
                    f"{DBTypeEnum.AUCTIONS}{db_type_str.split('-')[0]}"
                )
            else:
                db_type = DBType.from_str(DBTypeEnum.COMMODITIES)

            ext = m.group("ext")
            new_fn = DBFileName(
                namespace=name_space,
                db_type=db_type,
                ext=ext,
            )
            src = os.path.join(db_path, curr_fn)
            dst = os.path.join(db_path, str(new_fn))
            move(src, dst)
            continue

        if curr_fn == "meta-tw.json":
            new_fn = DBFileName(
                namespace=name_space,
                db_type=DBTypeEnum.META,
                ext=DBExtEnum.JSON,
            )
            src = os.path.join(db_path, curr_fn)
            dst = os.path.join(db_path, str(new_fn))
            move(src, dst)


def main(db_path: str = None):
    rename_db_files(db_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_path",
        type=str,
        default="/tmp/ah_db",
    )
    args = parser.parse_args()
    main(**vars(args))
