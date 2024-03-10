"""Database functions"""

# Imports --------------------------------------------------------------------

import os

# Functions ------------------------------------------------------------------

def get_connection_string() -> str:

    connection_string = \
        f"host={os.getenv('DB_HOST')} " \
        f"port={os.getenv('DB_PORT')} " \
        f"dbname={os.getenv('DB_NAME')} " \
        f"user={os.getenv('DB_USER')} " \
        f"password={os.getenv('DB_PASS')} "
    
    return connection_string
        