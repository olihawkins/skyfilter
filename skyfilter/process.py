"""Process posts"""

# Imports --------------------------------------------------------------------

import os

from atproto import Client

# Functions ------------------------------------------------------------------

def get_client() -> Client:
    client = Client()
    client.login(os.getenv("BSKY_USER"), os.getenv("BSKY_PASS"))
    return client

def fetch_post_thread(uri: str, client: Client = None) -> str:
    if client is None:
        client = get_client()
    post_thread = client.get_post_thread(uri, depth=0)
    return post_thread.model_dump_json()