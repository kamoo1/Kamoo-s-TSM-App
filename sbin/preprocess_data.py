#!/usr/bin/env python3
import os
import sys
import json
import argparse
from typing import Dict


class DataPreprocessor:
    FIELDS_TO_KEEP_BONUSES = {"level", "base_level", "curveId"}

    @classmethod
    def load_json(cls, path: str):
        with open(path) as f:
            return json.load(f)

    @classmethod
    def dump_json(cls, path: str, data: Dict):
        with open(path, "w") as f:
            json.dump(data, f, indent=4)

    @classmethod
    def add_curve_points(cls, data: Dict, curves: Dict, curve_id: int):
        curve = curves[str(curve_id)]
        new_points = []
        for point in curve["points"]:
            new_points.append(
                (
                    point["playerLevel"],
                    point["itemLevel"],
                )
            )
        data["points"] = new_points
        return data

    @classmethod
    def join_bonuses_and_curves(cls, bonuses: Dict, curves: Dict) -> Dict:
        new_bonuses = {}
        # go over all item of bonuses, remove all fields except FIELDS_TO_KEEP_BONUSES
        for k, v in bonuses.items():
            # nk = int(k) # it's JSON, we can't use int as key
            nk = k
            nv = {k_: v_ for k_, v_ in v.items() if k_ in cls.FIELDS_TO_KEEP_BONUSES}
            if "curveId" in nv:
                nv = cls.add_curve_points(nv, curves, nv["curveId"])

            new_bonuses[nk] = nv

        return new_bonuses

    @classmethod
    def run(cls, data_path: str, output_path: str):
        data_bonuses = cls.load_json(os.path.join(data_path, "bonuses.json"))
        data_curves = cls.load_json(os.path.join(data_path, "item-curves.json"))
        bonuses = cls.join_bonuses_and_curves(data_bonuses, data_curves)
        cls.dump_json(output_path, bonuses)


def main(data_path: str = None, output_path: str = None):
    DataPreprocessor.run(data_path, output_path)


def parse_args(raw_args):
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_path", help="Path to data", default="./data", type=str)
    parser.add_argument(
        "--output_path",
        help="Path to output",
        default="./ah/data/bonuses_curves.json",
        type=str,
    )
    args = parser.parse_args(raw_args)
    return args


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    main(**vars(args))
