def py(s):
    from ast import literal_eval
    return literal_eval(s)


def json(s):
    import json
    return json.loads(s)


def auto(s):
    if s in ("True", "TRUE", "true"):
        return True
    if s in ("False", "FALSE", "false"):
        return False

    try:
        return int(s)
    except (TypeError, ValueError):
        pass

    try:
        return float(s)
    except (TypeError, ValueError):
        pass

    try:
        return json.loads(s)
    except (TypeError, ValueError, json.JSONDecodeError):
        pass

    return s
