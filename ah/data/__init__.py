import os
import json
from typing import Dict

__all__ = ("map_bonuses",)


def load_json(filename: str) -> Dict:
    path = os.path.join(os.path.dirname(__file__), filename)
    with open(path) as f:
        return json.load(f)


def key_to_int(d: Dict) -> Dict:
    return {int(k): v for k, v in d.items()}


map_bonuses = load_json("bonuses_curves.json")
map_bonuses = key_to_int(map_bonuses)
