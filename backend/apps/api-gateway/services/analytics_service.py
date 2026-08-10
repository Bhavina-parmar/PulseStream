from repositories import analytics_repository

async def get_event_counter(event_type: str) -> int:
    return await analytics_repository.get_counter(event_type)

async def get_all_event_counters() -> dict:
    return await analytics_repository.get_all_counters()
