"""Stream data from the Bluesky firehose and process results asynchronously"""

# Imports ----------------------------------------------------------------------------------------

import asyncio
import psycopg

from atproto import AsyncFirehoseSubscribeReposClient
from atproto import parse_subscribe_repos_message
from atproto import firehose_models as fm
from atproto import models
from atproto import Client
from typing import Callable

from skyfilter.operations import get_ops_by_type
from skyfilter.utils import str_squish

# Message handler --------------------------------------------------------------------------------

def get_message_handler(queue: asyncio.Queue) -> Callable[[fm.MessageFrame], None]:

    async def message_handler(message: fm.MessageFrame) -> None:

        commit = parse_subscribe_repos_message(message)

        # Check that it's a commit message with .blocks inside
        if not isinstance(commit, models.ComAtprotoSyncSubscribeRepos.Commit):
            return

        if not commit.blocks:
            return

        # Get the operations by type from the commit
        ops = get_ops_by_type(commit)

        # Process each post in created
        for post in ops["posts"]["created"]:

            # Get URI and post record
            uri = post["uri"]
            record = post["record"]

            # Process record if not empty        
            if record is not None and record.model_dump is not None:

                # Convert record to dictionary
                record = record.model_dump()

                # Impose filter rules
                try:
                    
                    # Check there are languages specified
                    if record["langs"] is None:
                        return
                    
                    # Check English is a specified language
                    if "en" not in record["langs"]:
                        return
                    
                    # Check there is text
                    if record["text"] is None:
                        return
                    
                    # Check text is not empty
                    if len(record["text"]) == 0:
                        return
                    
                    # Check there is embedded data 
                    if record["embed"] is None:
                        return

                    # Check there are images
                    if "images" not in record["embed"].keys() and \
                            ("media" not in record["embed"].keys() or \
                            "images" not in record["embed"]["media"].keys()):
                        return
                    
                    # Add the message data to the queue
                    print(record)
                    await queue.put({
                        "uri": uri,
                        "record": record
                    })
                                
                except Exception as e:
                    print(e)
                    break

        # Process each post in deleted: todo

    return message_handler

# Message recorder -------------------------------------------------------------------------------

async def message_recorder(queue: asyncio.Queue) -> None:
    dsn = ""
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            while True:
                try:
                    post = await queue.get()
                    post_uri = post["uri"]
                    post_text = str_squish(post["record"]["text"])
                    post_created_at = post["record"]["created_at"]
                    sql = """
                        INSERT INTO posts (
                            post_uri, 
                            post_text,
                            post_created_at) 
                        VALUES (%s, %s, %s);
                        """
                    cur.execute(sql, (post_uri, post_text, post_created_at))
                    conn.commit()
                    queue.task_done()
                except Exception as e:
                    print(e)
                    conn.rollback()
                    break

# Stream from firehose ---------------------------------------------------------------------------

async def run(lifetime: int) -> None:

    # Create client
    client = AsyncFirehoseSubscribeReposClient()

    # Create queue
    queue = asyncio.Queue()

    # Create message handler
    message_handler = get_message_handler(queue)
    handler_task = asyncio.create_task(client.start(message_handler))

    # Create message recorder
    #message_recorder = get_message_recorder(queue)
    recorder_task = asyncio.create_task(message_recorder(queue))
    
    # Run for lifetime seconds
    await asyncio.sleep(lifetime)

    # Shut down tasks when complete
    await client.stop()
    await handler_task
    await queue.join()
    recorder_task.cancel()

# Get data for a post ----------------------------------------------------------------------------

def get_post_thread(uri: str) -> str:
    client = Client()
    client.login("", "")
    post_thread = client.get_post_thread(uri, depth=0)
    return post_thread.model_dump_json()