import os
import re
import argparse


def move(src, dst):
    print(f"Moving {src} to {dst}")
    # we are under same directory
    os.rename(src, dst)


def rename_db_files(db_path: str):
    mvs = [
        # 5375
        ("dynamic-tw_auctions5735.gz", "dynamic-tw_auctions_5735.gz"),
        # 5376
        ("dynamic-tw_auctions5736.gz", "dynamic-tw_auctions_5736.gz"),
        # 963
        ("dynamic-tw_auctions963.gz", "dynamic-tw_auctions_963.gz"),
        # 966
        ("dynamic-tw_auctions966.gz", "dynamic-tw_auctions_966.gz"),
        # 980
        ("dynamic-tw_auctions980.gz", "dynamic-tw_auctions_980.gz"),
        ("dynamic-tw_commodities.gz", "dynamic-tw_commodities.gz"),
        ("dynamic-tw_meta.json", "dynamic-tw_meta.json"),
    ]
    for src, dst in mvs:
        move(os.path.join(db_path, src), os.path.join(db_path, dst))


def main(db_path: str = None):
    before_fns = list(os.listdir(db_path))
    print(f"Before files: {before_fns}")
    rename_db_files(db_path)
    before_fns = list(os.listdir(db_path))
    print(f"After files: {before_fns}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_path",
        type=str,
        default="/tmp/ah_db",
    )
    args = parser.parse_args()
    main(**vars(args))
