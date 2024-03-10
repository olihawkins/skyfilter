# Get data from the Bluesky firehose

# Imports ----------------------------------------------------------------------------------------

import asyncio
import json

from atproto import AsyncFirehoseSubscribeReposClient
from atproto import parse_subscribe_repos_message
from atproto import firehose_models as fm
from atproto import models
from atproto import Client
from typing import Callable

from skyfilter.operations import get_ops_by_type

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
            rec = post["record"]

            # Process record if not empty        
            if rec is not None and rec.model_dump is not None:

                # Convert record to dictionary
                rec = rec.model_dump()

                # Impose filter rules
                try:
                    if rec["langs"] is not None and "en" in rec["langs"]:
                        if rec["embed"] is not None:
                            if "images" in rec["embed"].keys() or \
                            ("media" in rec["embed"].keys() and \
                            "images" in rec["embed"]["media"].keys()):
                                
                                await queue.put({
                                    "uri": uri,
                                    "record": rec
                                })
                                
                except Exception as e:
                    print(e)

        # Process each post in deleted: todo

    return message_handler

# Message recorder -------------------------------------------------------------------------------

def get_message_recorder(queue: asyncio.Queue):

    async def message_recorder() -> None:
        while True:
            post = await queue.get()
            with open("output.json", "a") as f:
                f.write(json.dumps(post))
                f.write(",\n")
            queue.task_done()

    return message_recorder

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
    message_recorder = get_message_recorder(queue)
    recorder_task = asyncio.create_task(message_recorder())
    
    # Run for lifetime seconds
    await asyncio.sleep(lifetime)

    # Shut down tasks when complete
    await client.stop()
    await handler_task
    await queue.join()
    recorder_task.cancel()

# Get data for a post ----------------------------------------------------------------------------

def get_post_thread(client: Client, uri: str) -> str:
    # client = Client()
    # client.login("olihawkins.bsky.social", "")
    post_thread = client.get_post_thread(uri, depth=0)
    return post_thread.model_dump_json()