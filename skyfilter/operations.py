"""Get operations by type from an atproto commit"""

# Imports --------------------------------------------------------------------

from atproto import CAR
from atproto import models
from atproto import AtUri

# Get operations by type -----------------------------------------------------

def get_ops_by_type(
        commit: models.ComAtprotoSyncSubscribeRepos.Commit) -> dict:

    operation_by_type = {
        "posts": {"created": [], "deleted": []},
        "reposts": {"created": [], "deleted": []},
        "likes": {"created": [], "deleted": []},
        "follows": {"created": [], "deleted": []},
    }

    blocks_bytes = commit.blocks.encode("utf-8") \
        if isinstance(commit.blocks, str) else commit.blocks
    
    car = CAR.from_bytes(blocks_bytes)
    
    for op in commit.ops:
        uri = AtUri.from_str(f"at://{commit.repo}/{op.path}")

        if op.action == "update":
            continue

        if op.action == "create":
            if not op.cid:
                continue

            create_info = {
                "uri": str(uri), 
                "cid": str(op.cid), 
                "author": commit.repo}

            record_raw_data = car.blocks.get(op.cid)

            if not record_raw_data:
                continue

            record = models.get_or_create(record_raw_data, strict=False)
            
            # Type errors ignored below because atproto does not export the 
            # ModelBase and DotDict classes needed for explicit checks

            if uri.collection == models.ids.AppBskyFeedLike and \
                    models.is_record_type(
                        record, models.ids.AppBskyFeedLike): # type: ignore

                operation_by_type["likes"]["created"].append(
                    {"record": record, **create_info})
            
            elif uri.collection == models.ids.AppBskyFeedPost and \
                    models.is_record_type(
                        record, models.ids.AppBskyFeedPost): # type: ignore
                
                operation_by_type["posts"]["created"].append(
                    {"record": record, **create_info})
            
            elif uri.collection == models.ids.AppBskyFeedRepost and \
                    models.is_record_type(
                        record, models.ids.AppBskyFeedRepost): # type: ignore
                
                operation_by_type["reposts"]["created"].append(
                    {"record": record, **create_info})
            
            elif uri.collection == models.ids.AppBskyGraphFollow and \
                models.is_record_type(
                    record, models.ids.AppBskyGraphFollow): # type: ignore

                operation_by_type["follows"]["created"].append(
                    {"record": record, **create_info})

        if op.action == "delete":
            if uri.collection == models.ids.AppBskyFeedLike:
                operation_by_type["likes"]["deleted"].append(
                    {"uri": str(uri)})
            elif uri.collection == models.ids.AppBskyFeedPost:
                operation_by_type["posts"]["deleted"].append(
                    {"uri": str(uri)})
            elif uri.collection == models.ids.AppBskyFeedRepost:
                operation_by_type["reposts"]["deleted"].append(
                    {"uri": str(uri)})
            elif uri.collection == models.ids.AppBskyGraphFollow:
                operation_by_type["follows"]["deleted"].append(
                    {"uri": str(uri)})

    return operation_by_type