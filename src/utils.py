import json

from typing import Dict
from pathlib import Path


def write_str_to_file(string: str, full_path: Path) -> str:
    with open(full_path, "w") as file:
        file.write(string)

    return full_path


def extract_json_from_str(text: str) -> Dict:
    start = text.find("{")
    end = text.rfind("}") + 1
    extracted = text[start:end]

    if extracted:
        return json.loads(extracted)
    else:
        raise ValueError("No valid JSON found")
