"""Parse and select specific information from
JSON data using a subset of Jq-like selectors."""

import json
import re

# Regex to match .key, .key[], .key[N], .[N]
_re_selector = re.compile(r'(?:\.([a-zA-Z0-9_]+)|\[(\d*)\])')


def select(jobj, selector, default=None):
    """
    Extract information from a JSON string using a subset of Jq-like selectors.
    Supported selectors:
      - .key
      - .key1.key2
      - .key[]
      - .key[N]
      - .key1.key2[]
      - .key1.key2[N]
      - .[N] (select N-th element from root array)
      - . (returns the whole object)
    """
    if isinstance(jobj, str):
        try:
            data = json.loads(jobj)
        except Exception:
            return default
    else:
        data = jobj

    selector = selector.strip()
    if selector == '.':
        return data
    if not selector.startswith('.'):
        raise ValueError("Selector must start with '.'")

    parts = _re_selector.findall(selector)
    if not parts:
        raise ValueError("Invalid selector syntax")

    def _extract(obj, parts):
        if not parts:
            return obj
        key, idx_str = parts[0]
        if key:
            if not isinstance(obj, dict) or key not in obj:
                return None
            value = obj[key]
            # Check if next part is an index or []
            if len(parts) > 1 and parts[1][0] == '' and parts[1][1] != '':  # [N]
                idx = int(parts[1][1])
                if not isinstance(value, list) or idx < 0 or idx >= len(value):
                    return None
                return _extract(value[idx], parts[2:])
            elif len(parts) > 1 and parts[1][0] == '' and parts[1][1] == '':  # []
                if not isinstance(value, list):
                    return None
                return [_extract(item, parts[2:]) for item in value]
            else:
                return _extract(value, parts[1:])
        else:  # .[N] at root or after array
            if not isinstance(obj, list):
                return None
            if idx_str == '':  # []
                return [_extract(item, parts[1:]) for item in obj]
            idx = int(idx_str)
            if idx < 0 or idx >= len(obj):
                return None
            return _extract(obj[idx], parts[1:])
    return _extract(data, parts)
