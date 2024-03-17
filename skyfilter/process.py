"""Process posts that have been saved in the database"""

# Imports --------------------------------------------------------------------

import asyncio
import datetime
import logging
import requests
import os
import psycopg

from atproto import AsyncClient
from dotenv import load_dotenv

from skyfilter import database as db
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

# Get image filepath from url ------------------------------------------------

def get_image_download_path(image_url: str) -> str:

    # Get image suffix
    image_suffix = image_url.split("@")[-1]

    # Get image name
    image_name = image_url.split("/")[-1]
    image_name = image_name.split("@")[0]

    # Construct filename
    image_filename = f"{image_name}.{image_suffix}"
   
    # Extract filepath components
    filepath_dirs = str(os.getenv("SF_DB_IMAGES_DIR")).split("/")

    # Get date directory (and create the directory if it doesn't exist)
    date_dir = datetime.date.today().isoformat()
    os.makedirs(os.path.join(*filepath_dirs, date_dir), exist_ok=True)

    # Combine components with name
    image_filepath = os.path.join(*filepath_dirs, date_dir, image_filename)
    return image_filepath

# Fetch post image -----------------------------------------------------------

async def fetch_image(post_image: dict) -> dict:
    
    # Get image locations
    image_url = post_image["fullsize"]
    image_filepath = get_image_download_path(image_url)

    # Compile data
    image = {
        "complete": False,
        "url": image_url,
        "filepath": image_filepath,
        "alt": post_image["alt"],
        "height": post_image["aspect_ratio"]["height"],
        "width": post_image["aspect_ratio"]["width"]
    }
    
    try:
        response = requests.get(
            image_url, 
            allow_redirects=True,
            timeout=60)

        if response.status_code == 200:
            image["complete"] = True
        else:
            raise Exception
        
        with open(image_filepath, "wb") as f:
            f.write(response.content)
        
    except Exception as e:
        logger.error(f"Error in fetch_image: {e}")
    
    return image

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
    
    # Initialise uncatalogued result
    result = { 
        "status": db.POST_STATUS_UNCATALOGUED,
        "uri": uri 
    }

    # Fetch post images
    post_images = await fetch_post_images(uri, client)
    
    # If no post images, return fetch post error
    if len(post_images) == 0:
        result["status"] = db.POST_STATUS_FETCH_POST_ERROR
        return result
    
    # Fetch images
    images = await fetch_images(post_images)

    # If no images, return fetch image error
    if len(images) == 0:
        result["status"] = db.POST_STATUS_FETCH_IMAGE_ERROR
        return result
    
    # Update result
    result["images"] = images
    
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