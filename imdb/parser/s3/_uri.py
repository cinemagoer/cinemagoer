# Copyright 2026 Davide Alberani <da@mimante.net>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

"""Private helpers for safely displaying database URIs."""

import re

_PASSWORD_RE = re.compile(r'(://[^/@\s:]+:)[^/@\s]*(?=@)')
_SECRET_QUERY_RE = re.compile(
    r'([?&](?:access_token|api_key|auth_token|client_secret|credentials|'
    r'password|passwd|pwd|secret|token)=)'
    r'[^&#\s]*',
    re.IGNORECASE,
)


def redact_uri_secrets(value):
    """Return *value* with credentials and common URI secrets hidden."""
    value = str(value)
    value = _PASSWORD_RE.sub(r'\1***', value)
    return _SECRET_QUERY_RE.sub(r'\1***', value)
