"""Process posts that have been saved in the database"""

# Imports --------------------------------------------------------------------

import asyncio
import logging
import os
import psycopg
import signal

from atproto import AsyncClient

from skyfilter.utils import nested_key_exists

# Get a client ---------------------------------------------------------------

async def get_client() -> AsyncClient:
    client = AsyncClient()
    await client.login(
        os.getenv("BSKY_USER"), 
        os.getenv("BSKY_PASS"))
    return client

# Fetch a post thread --------------------------------------------------------

async def fetch_post_thread(
        uri: str, 
        client: AsyncClient | None = None) -> dict:

    if client is None:
        client = await get_client()

    post_thread = await client.get_post_thread(uri, depth=0)
    return post_thread.model_dump()

# Fetch post image URLs ------------------------------------------------------

async def fetch_post_images(
        uri: str, 
        client: AsyncClient) -> list:

    post_thread = await fetch_post_thread(uri, client)
    images_keys = ["thread", "post", "embed", "images"]
    images = []

    if nested_key_exists(post_thread, images_keys):
        for image in post_thread["thread"]["post"]["embed"]["images"]:
            images.append(image)

    return images