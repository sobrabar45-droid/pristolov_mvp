import json
from pathlib import Path

import yaml


def load_yaml_file(file_path: Path):
    with file_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def safe_list_length(data: dict, key: str) -> int:
    if not isinstance(data, dict):
        return 0
    value = data.get(key, [])
    return len(value) if isinstance(value, list) else 0


def dump_json(value):
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False)


def load_json_text(value):
    if value is None:
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return value


def house_key_allowed(task_allowed_house_keys_raw, house_key: str) -> bool:
    allowed = load_json_text(task_allowed_house_keys_raw)

    if allowed in (None, "", []):
        return True

    if isinstance(allowed, list):
        return house_key in allowed

    return True