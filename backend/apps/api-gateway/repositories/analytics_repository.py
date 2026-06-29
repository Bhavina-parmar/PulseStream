from config.redis import redis_client
KNOWN_EVENT_TYPES=[
    "USER_LOGIN",
    "PAGE_VIEW",
    "BUTTON_CLICK",
    "SEARCH",
    "FILE_UPLOAD",
    "PURCHASE"
]

def increment_counter(event_type: str)->int:
    key=f"analytics:{event_type}"
    return redis_client.incr(key)

def get_counter(event_type:str)->int:
    key=f"analytics:{event_type}"
    value = redis_client.get(key)
    if value is None:
        return 0
    return int(value) if value else 0

def get_all_counters()->dict:
    return {event_type:get_counter(event_type) for event_type in KNOWN_EVENT_TYPES}