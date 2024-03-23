"""Utility functions"""

# Imports --------------------------------------------------------------------

import re
import signal

from types import FrameType

# Signal monitor class -------------------------------------------------------
    
class SignalMonitor:
    
    shutdown = False
  
    def __init__(self, name, logger) -> None:
        self.name = name
        self.logger = logger
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def exit(self, signum: int, frame: FrameType | None) -> None:
        print(f"{self.name} shutting down")
        self.logger.info(f"{self.name} shutting down")
        self.shutdown = True

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
