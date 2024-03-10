"""Stream data from the Bluesky firehose and process results asynchronously"""

# Imports ----------------------------------------------------------------------------------------

import asyncio
import logging
import os
import psycopg
import signal

from atproto import AsyncFirehoseSubscribeReposClient
from atproto import parse_subscribe_repos_message
from atproto import firehose_models as fm
from atproto import models
from dotenv import load_dotenv
from types import FrameType
from typing import Callable

from skyfilter.database import get_connection_string
from skyfilter.operations import get_ops_by_type
from skyfilter.utils import str_squish

# Setup ------------------------------------------------------------------------------------------

# Load environment variables
load_dotenv()

# Create logger
logger = logging.getLogger(__name__)

# Signal monitor ---------------------------------------------------------------------------------
    
class SignalMonitor:
    
    shutdown = False
  
    def __init__(self) -> None:
        signal.signal(signal.SIGINT, self.exit)
        signal.signal(signal.SIGTERM, self.exit)

    def exit(self, signum: int, frame: FrameType) -> None:
        self.shutdown = True

# Message handler --------------------------------------------------------------------------------

def get_message_handler(queue: asyncio.Queue) -> Callable[[fm.MessageFrame], None]:

    async def message_handler(message: fm.MessageFrame) -> None:

        commit = parse_subscribe_repos_message(message)

        # Check that the message is a commit with .blocks inside
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
                    
                    # Check there is a field for languages
                    if record["langs"] is None:
                        return
                    
                    # Check English is a specified language
                    if "en" not in record["langs"]:
                        return
                    
                    # Check there is a field for text
                    if record["text"] is None:
                        return
                    
                    # Check text is not empty
                    if len(record["text"]) == 0:
                        return
                    
                    # Check there is a field for embedded data 
                    if record["embed"] is None:
                        return

                    # Check the embedded data contains images
                    if "images" not in record["embed"].keys() and \
                            ("media" not in record["embed"].keys() or \
                            "images" not in record["embed"]["media"].keys()):
                        return
                    
                    # Add the message data to the queue
                    await queue.put({
                        "uri": uri,
                        "record": record
                    })
                                
                except Exception as e:
                    logger.error(f"Error in get_message_handler: {e}")

        # Process each post in deleted: todo

    return message_handler

# Message recorder -------------------------------------------------------------------------------

async def message_recorder(queue: asyncio.Queue) -> None:
    dsn = get_connection_string()
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
                    logger.error(f"Error in message_recorder: {e}")
                    conn.rollback()

# Stream from firehose ---------------------------------------------------------------------------

async def stream(
        lifecycle: int = 10,
        logfile: str = os.path.join("logs", "stream.log")) -> None:

    # Create logger
    logging.basicConfig(
        filename=logfile, 
        filemode="w", 
        format="%(asctime)s - %(levelname)s - %(message)s", 
        level=logging.INFO)

    logger.info("Stream starting")

    # Create signal monitor
    signal_monitor = SignalMonitor()

    # Create client
    client = AsyncFirehoseSubscribeReposClient()

    # Create queue
    queue = asyncio.Queue()

    # Create message handler
    message_handler = get_message_handler(queue)
    handler_task = asyncio.create_task(client.start(message_handler))

    # Create message recorder
    recorder_task = asyncio.create_task(message_recorder(queue))
    
    # Run for lifecycle seconds
    while not signal_monitor.shutdown:
        await asyncio.sleep(lifecycle)

    logger.info("Stream shutting down")

    # Shut down tasks when complete
    await client.stop()
    await handler_task
    await queue.join()
    recorder_task.cancel()

# Main -------------------------------------------------------------------------------------------
    
if __name__ == '__main__':
    asyncio.run(stream())
  