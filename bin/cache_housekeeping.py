import os
import sys
import re
import glob
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

def rm_us_eu_files(db_path: str):
    # remove *us* and *eu* files
    for fn in os.listdir(db_path):
        if re.search(r"us|eu", fn):
            os.remove(os.path.join(db_path, fn))

def exec(command: str):
    # run bash command
    print(f"Running command: {command}")
    os.system(command)


def main(db_path: str = None):
    before_fns = list(os.listdir(db_path))
    print(f"Before files: {before_fns}")
    # rename_db_files(db_path)
    # exec(f"cd {db_path} && rm *classic*")
    rm_us_eu_files(db_path)
    after_fns = list(os.listdir(db_path))
    print(f"After files: {after_fns}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_path",
        type=str,
        default="/tmp/ah_db",
    )
    args = parser.parse_args()
    main(**vars(args))
