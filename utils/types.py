def _to_safe_string(val):  # safe string (for slicing)
    return val or ""

def _to_safe_list(val):  # safe list
    if isinstance(val, list): return val
    if isinstance(val, str):
        try:
            v = json.loads(val)
            return v if isinstance(v, list) else []
        except Exception:
            return []
    return []

def _to_safe_dict(val):  # safe dict
    if isinstance(val, dict): return val
    if isinstance(val, str):
        try: 
            v = json.loads(val)
            return v if isinstance(v, dict) else {}
        except Exception:
            return {}
    return {}

def _to_safe_float(val, default=0.0):  # safe float
    try:
        return float(val if val is not None else default)
    except Exception:
        return default
