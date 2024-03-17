"""Utility functions"""

# Imports --------------------------------------------------------------------

import re

# Squish string --------------------------------------------------------------

def str_squish(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

# Check dictionary for nested key --------------------------------------------

def nested_key_exists(data: dict, keys: list) -> bool:
    try:
        for key in keys:
            data = data[key]
        return True
    except (KeyError, TypeError):
        return False
