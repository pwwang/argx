"""Additional types for argx"""
from typing import Any


def py(s: str) -> Any:
    from ast import literal_eval
    return literal_eval(s)


def json(s: str) -> Any:
    import json
    return json.loads(s)


def auto(s: str) -> Any:
    if s in ("True", "TRUE", "true"):
        return True
    if s in ("False", "FALSE", "false"):
        return False
    if s in ("None", "NONE", "none"):
        return None

    try:
        return int(s)
    except (TypeError, ValueError):
        pass

    try:
        return float(s)
    except (TypeError, ValueError):
        pass

    import json
    try:
        return json.loads(s)
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    return s
