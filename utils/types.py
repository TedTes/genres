def _to_safe_string(val):  # safe string (for slicing)
    return val or ""

def _to_safe_lst(val):  # safe list
    return val or []

def _to_safe_dict(val):  # safe dict
    return val or {}

def _to_safe_float(val, default=0.0):  # safe float
    try:
        return float(val if val is not None else default)
    except Exception:
        return default
