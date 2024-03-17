"""Process posts that have been saved in the database"""

# Imports --------------------------------------------------------------------

import asyncio
import logging
import os
import psycopg
import signal

from atproto import AsyncClient
from dotenv import load_dotenv

from skyfilter.utils import nested_key_exists

# Setup ----------------------------------------------------------------------

# Load environment variables
load_dotenv()

# Create logger
logger = logging.getLogger(__name__)

# Get a client ---------------------------------------------------------------

async def get_client() -> AsyncClient:
    client = AsyncClient()
    await client.login(
        os.getenv("SF_BSKY_USER"), 
        os.getenv("SF_BSKY_PASS"))
    return client

# Fetch a post thread --------------------------------------------------------

async def fetch_post(
        uri: str, 
        client: AsyncClient) -> dict:

    # Initialise empty post
    post = {}

    try:
        
        # Fetch post thread and convert to dict
        post_thread = await client.get_post_thread(uri, depth=0)
        post_thread = post_thread.model_dump()

        # Extract post from thread
        post_keys = ["thread", "post"]
        if nested_key_exists(post_thread, post_keys):
            post = post_thread["thread"]["post"]
    
    except Exception as e:
        logger.error(f"Error in fetch_post: {e}")
        pass

    return post

# Fetch post image URLs ------------------------------------------------------

async def fetch_post_images(
        uri: str, 
        client: AsyncClient) -> list:

    post = await fetch_post(uri, client)
    post_images_keys = ["embed", "images"]
    post_images = []

    if nested_key_exists(post, post_images_keys):
        for post_image in post["embed"]["images"]:
            post_images.append(post_image)

    return post_images

# Fetch post image -----------------------------------------------------------

async def fetch_image(post_image: dict) -> dict:
    return {}

# Fetch post images ----------------------------------------------------------

async def fetch_images(post_images: list) -> list:

    # Fetch images asynchronously
    images = await asyncio.gather(
        *(fetch_image(post_image) for post_image in post_images))
    
    # Check if all images were fetched
    fetch_errors = False
    for image in images:
        if not image["complete"]:
            fetch_errors = True
    
    # If there were fetch errors, rollback all fetches
    if fetch_errors: 
        for image in images:
            if image["complete"]:
                os.remove(image["filepath"])
        images = []
        
    return images

# Process post ---------------------------------------------------------------

async def process_post(
        uri: str, 
        client: AsyncClient) -> dict:
    
    # Initialise incomplate result
    result = { 
        "complete": False,
        "uri": uri 
    }

    # Fetch post images
    post_images = await fetch_post_images(uri, client)
    
    if len(post_images) == 0:
        return result
    
    # Fetch images
    images = await fetch_images(post_images)

    if len(images) == 0:
        return result
    
    # Classify images

    return result


# Process post ---------------------------------------------------------------

async def process(
        logfile: str = os.path.join("logs", "process.log")) -> None:

    # Create logger
    logging.basicConfig(
        filename=logfile, 
        filemode="w", 
        format="%(asctime)s - %(levelname)s - %(message)s", 
        level=logging.INFO)

    logger.info("Process starting")

# Main -----------------------------------------------------------------------
    
if __name__ == '__main__':
    asyncio.run(process())