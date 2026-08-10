import json 
from aiokafka import AIOKafkaProducer
from config.settings import settings

_producer : AIOKafkaProducer | None = None

async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        await _producer.start()
    return _producer

async def publish_event(topic: str, event_data: dict):
    producer = await get_producer()
    await producer.send_and_wait(topic, event_data)

async def stop_producer():
    global _producer
    if _producer is not None:
        await _producer.stop()
        _producer = None