import json 
from aiokafka import AIOKafkaProducer
from config.settings import settings

async def publish_event(topic: str, event_data: dict):
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer= lambda v: json.dumps(v, default=str).encode('utf-8')
    )

    await producer.start()
    try:
        await producer.send_and_wait(topic, event_data)
    finally:
        await producer.stop()