"""Utility functions"""

# Imports --------------------------------------------------------------------

import re

# Functions ------------------------------------------------------------------

def str_squish(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())