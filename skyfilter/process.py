"""Process posts that have been saved in the database"""

# Imports --------------------------------------------------------------------

import asyncio
import logging
import requests
import numpy as np
import time
import os
import psycopg

from atproto import AsyncClient
from datetime import date
from datetime import datetime
from dotenv import load_dotenv
from psycopg.rows import dict_row

from skyfilter import database as db
from skyfilter.utils import nested_key_exists
from skyfilter.utils import SignalMonitor

# Setup ----------------------------------------------------------------------

# Load environment variables
load_dotenv()

# Create logger
logger = logging.getLogger(__name__)

# Create RNG
RNG = np.random.default_rng()

# Get a client ---------------------------------------------------------------

async def get_client() -> AsyncClient:
    client = AsyncClient()
    await client.login(
        os.getenv("SF_BSKY_USER"), 
        os.getenv("SF_BSKY_PASS"))
    return client

# Fetch the rate limit remaining: hacky, don't use in prod -------------------

async def fetch_rate_limit_remaining(client: AsyncClient) -> int:
    try:
        response = await client.get_post_thread("at://did.plc", depth=0)
        return 0
    except Exception as e:
        return int(e.response.headers["RateLimit-Remaining"]) # type: ignore

# Fetch a post thread --------------------------------------------------------

async def fetch_post(
        client: AsyncClient,
        uri: str) -> dict:

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
        client: AsyncClient,
        post_uri: str) -> list:

    post = await fetch_post(client, post_uri)
    post_images = []

    if nested_key_exists(post, ["embed", "images"]):
        for post_image in post["embed"]["images"]:
            post_images.append(post_image)

    if nested_key_exists(post, ["embed", "media", "images"]):
        for post_image in post["embed"]["media"]["images"]:
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
    date_dir = date.today().isoformat()
    os.makedirs(os.path.join(*filepath_dirs, date_dir), exist_ok=True)

    # Combine components with name
    image_filepath = os.path.join(*filepath_dirs, date_dir, image_filename)
    return image_filepath

# Delete images --------------------------------------------------------------

def delete_images(images: list) -> list:
    for image in images:
        if image["complete"]:
            os.remove(image["filepath"])
    return []

# Fetch post image -----------------------------------------------------------

async def fetch_image(post_image: dict) -> dict:
    
    # Get image locations
    image_url = post_image["fullsize"]
    image_filepath = get_image_download_path(image_url)

    # Get image params
    height = None
    width = None

    if post_image["aspect_ratio"] is not None:
        height = post_image["aspect_ratio"]["height"]
        width = post_image["aspect_ratio"]["width"]

    # Compile data
    image = {
        "complete": False,
        "url": image_url,
        "filepath": image_filepath,
        "alt": post_image["alt"],
        "height": height,
        "width": width
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
    
    # If there were fetch errors, delete images for this post
    if fetch_errors: 
        images = delete_images(images)
         
    return images

# Classify images ------------------------------------------------------------

def classify_images(images: list) -> list:

    # Classify with pseudo error
    classify_errors = False
    for image in images:
        image["score"] = RNG.random()
        if image["score"] < 0.02:
            classify_errors = True

    # If there were classify errors, delete images for this post
    if classify_errors: 
        images = delete_images(images)

    return images

# Drop filter ----------------------------------------------------------------

def drop_random_negatives(images: list) -> bool:
    
    # Randomly drop negative results below threshold
    drop = False
    highest_score = np.max([image["score"] for image in images])
    if highest_score < 0.3 and RNG.random() < 0.5:
        delete_images(images)
        drop = True

    return drop

# Process post ---------------------------------------------------------------

async def process_post(
        client: AsyncClient,
        post_id: int,
        post_uri: str) -> dict:
    
    # Initialise uncatalogued result
    result = { 
        "status_id": db.POST_STATUS_UNCATALOGUED,
        "post_id": post_id,
        "post_uri": post_uri 
    }

    # Fetch post images
    post_images = await fetch_post_images(client, post_uri)
    
    # If no post images, return fetch post error
    if len(post_images) == 0:
        result["status_id"] = db.POST_STATUS_FETCH_POST_ERROR
        return result
    
    # Fetch images
    images = await fetch_images(post_images)

    # If fetch errors, return fetch image error
    if len(images) == 0:
        result["status_id"] = db.POST_STATUS_FETCH_IMAGE_ERROR
        return result
     
    # Classify images
    classified_images = classify_images(images)

    # If classify errors, return classify image error
    if len(classified_images) == 0:
        result["status_id"] = db.POST_STATUS_CLASSIFY_IMAGE_ERROR
        return result

    # Drop random negative posts
    drop = drop_random_negatives(classified_images)

    # If drop, return dropped
    if drop:
        result["status_id"] = db.POST_STATUS_DROPPED
        return result

    # Update result
    result["status_id"] = db.POST_STATUS_COMPLETE
    result["images"] = classified_images

    return result

# Get batch ------------------------------------------------------------------

def get_batch(batch_size: int) -> list:
    result = []
    dsn = db.get_connection_string()
    with psycopg.connect(dsn) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            try:
                sql = """
                    SELECT 
                        post_id, 
                        post_uri
                    FROM posts 
                    WHERE post_status_id = 1 
                    ORDER BY post_created_at 
                    LIMIT (%s);
                    """
                cur.execute(sql, (batch_size,))
                result = cur.fetchall()
            except Exception as e:
                logger.error(f"Error in process.get_batch: {e}")
    return result

# Process batch --------------------------------------------------------------

async def process_batch(client: AsyncClient, posts: list) -> list:

    # Create a generator of posts to process
    posts_generator = (process_post(
        client, 
        post["post_id"], 
        post["post_uri"]) for post in posts)
    
    # Run the generator on each post asynchronously
    results = await asyncio.gather(*posts_generator)

    # Save the results to the database
    dsn = db.get_connection_string()
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for result in results:
                try:
                    
                    sql = """
                        UPDATE posts 
                        SET post_status_id = (%s)
                        WHERE post_id = (%s);
                        """

                    params = (result["status_id"], result["post_id"])
                    cur.execute(sql, params)

                    if result["status_id"] == db.POST_STATUS_COMPLETE:
                        
                        for image in result["images"]:

                            sql = """
                                INSERT INTO images (
                                image_url,
                                image_filepath,
                                image_alt,
                                image_height,
                                image_width,
                                image_score,
                                post_id) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s);
                            """

                            params = (
                                image["url"],
                                image["filepath"],
                                image["alt"],
                                image["height"],
                                image["width"],
                                image["score"],
                                result["post_id"])
                            
                            cur.execute(sql, params)

                    conn.commit()

                except Exception as e:
                    logger.error(f"Error in process.process_batch: {e}")
                    conn.rollback()

    return results

# Process --------------------------------------------------------------------

async def process(
        logfile: str = os.path.join("logs", "process.log")) -> None:

    # Create logger
    logging.basicConfig(
        filename=logfile, 
        filemode="w", 
        format="%(asctime)s - %(levelname)s - %(message)s", 
        level=logging.INFO)

    logger.info("Process starting")

    # Create signal monitor
    signal_monitor = SignalMonitor("Process", logger)

    # Create client
    client = await get_client()

    # Set batch processing parameters
    batch_interval = 0.5
    batch_postpone = 0.5
    batch_wait = 4
    batch_size = 10

    # Set next update to a second before current time
    next_update = datetime.now().timestamp() - 1

    # Report running
    print("Process running")
    logger.info("Process running")

    # Run until shutdown signal
    while not signal_monitor.shutdown:

        # Get the current time
        now = datetime.now().timestamp()

        if now < next_update:
            time.sleep(batch_postpone)
            continue
        
        # Set the time for the next update
        next_update = now + batch_interval

        # Get batch of uncatalogued posts
        posts = get_batch(batch_size)

        # Wait if no posts to process
        if len(posts) == 0:
            time.sleep(batch_wait)

        await process_batch(client, posts)


# Main -----------------------------------------------------------------------
    
if __name__ == '__main__':
    asyncio.run(process())