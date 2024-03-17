"""Database functions"""

# Imports --------------------------------------------------------------------

import os

# Functions ------------------------------------------------------------------

def get_connection_string() -> str:

    connection_string = \
        f"host={os.getenv('SF_DB_HOST')} " \
        f"port={os.getenv('SF_DB_PORT')} " \
        f"dbname={os.getenv('SF_DB_NAME')} " \
        f"user={os.getenv('SF_DB_USER')} " \
        f"password={os.getenv('SF_DB_PASS')} "
    
    return connection_string
        