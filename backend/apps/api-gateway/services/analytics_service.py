from repositories import analytics_repository

def get_event_counter(event_type: str) -> int:
    return analytics_repository.get_counter(event_type)

def get_all_event_counters() -> dict:
    return analytics_repository.get_all_counters()
