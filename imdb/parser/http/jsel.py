import json
import re

_re_selector = re.compile(r'\.([a-zA-Z0-9_]+)(\[\])?')

def select(jstr, selector, default=None):
    """
    Extract information from a JSON string using a subset of Jq-like selectors.
    Supported selectors:
      - .key
      - .key1.key2
      - .key[]
      - .key1.key2[]
    """
    try:
        data = json.loads(jstr)
    except Exception:
        return default

    # Remove leading/trailing whitespace and ensure selector starts with '.'
    selector = selector.strip()
    if not selector.startswith('.'):
        raise ValueError("Selector must start with '.'")

    # Split selector into parts, handling [] for arrays
    parts = _re_selector.findall(selector)
    if not parts:
        raise ValueError("Invalid selector syntax")

    def extract(obj, parts):
        if not parts:
            return obj
        key, is_array = parts[0]
        if not isinstance(obj, dict) or key not in obj:
            return None
        value = obj[key]
        if is_array:
            if not isinstance(value, list):
                return None
            return [extract(item, parts[1:]) for item in value]
        else:
            return extract(value, parts[1:])

    return extract(data, parts)
