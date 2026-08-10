from config.redis import redis_client
KNOWN_EVENT_TYPES=[
    "USER_LOGIN",
    "PAGE_VIEW",
    "BUTTON_CLICK",
    "SEARCH",
    "FILE_UPLOAD",
    "PURCHASE"
]

async def increment_counter(event_type: str)->int:
    key=f"analytics:{event_type}"
    return await redis_client.incr(key)

async def get_counter(event_type:str)->int:
    key=f"analytics:{event_type}"
    value = await redis_client.get(key)
    return int(value) if value else 0

async def get_all_counters()->dict:
    results = {}
    for event_type in KNOWN_EVENT_TYPES:
        results[event_type] = await get_counter(event_type)
    return results