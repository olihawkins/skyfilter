"""Database functions"""

# Imports --------------------------------------------------------------------

import os

from typing import Final

# Constants ------------------------------------------------------------------

POST_STATUS_UNCATALOGUED: Final[int] = 1
POST_STATUS_BLOCKED: Final[int] = 2
POST_STATUS_FETCH_POST_ERROR: Final[int] = 3
POST_STATUS_FETCH_IMAGE_ERROR: Final[int] = 4
POST_STATUS_CLASSIFY_IMAGE_ERROR: Final[int] = 5
POST_STATUS_DROPPED: Final[int] = 6
POST_STATUS_COMPLETE: Final[int] = 7

# Functions ------------------------------------------------------------------

def get_connection_string() -> str:

    connection_string = \
        f"host={os.getenv('SF_DB_HOST')} " \
        f"port={os.getenv('SF_DB_PORT')} " \
        f"dbname={os.getenv('SF_DB_NAME')} " \
        f"user={os.getenv('SF_DB_USER')} " \
        f"password={os.getenv('SF_DB_PASS')} "
    
    return connection_string
        