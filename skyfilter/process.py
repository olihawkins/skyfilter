"""Process posts that have been saved in the database"""

# Imports --------------------------------------------------------------------

import asyncio
import logging
import os
import psycopg
import signal

from atproto import AsyncClient

from skyfilter.utils import check_nested_key

# Get a client ---------------------------------------------------------------

async def get_client() -> AsyncClient:
    client = AsyncClient()
    await client.login(os.getenv("BSKY_USER"), os.getenv("BSKY_PASS"))
    return client

# Fetch a post thread --------------------------------------------------------

async def fetch_post_thread(
        uri: str, 
        client: AsyncClient | None = None) -> dict:
    
    if client is None:
        client = await get_client()
    post_thread = await client.get_post_thread(uri, depth=0)
    return post_thread.model_dump()

