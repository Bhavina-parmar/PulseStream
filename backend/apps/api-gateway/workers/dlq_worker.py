import asyncio
import json
import logging
import signal
import sys
from kafka.topics import DLQ_TOPIC
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from prometheus_client import Counter, start_http_server
from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("dlq_worker")

KAFKA_BOOTSTRAP_SERVERS = settings.kafka_bootstrap_servers
CONSUMER_GROUP_ID = "dlq_processor_group"
PROMETHEUS_PORT = 8002

DLQ_EVENTS_TOTAL = Counter(
    "dlq_events_total",
    "Total count of dead-lettered events processed by DLQ worker",
    labelnames=["event_type"]
)

class DLQWorker:
    def __init__(self):
        self.consumer = None
        self.is_running = True

    async def start(self):
        logger.info(f"Connecting DLQ Worker to Kafka at {KAFKA_BOOTSTRAP_SERVERS}...")
        self.consumer = AIOKafkaConsumer(
            DLQ_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=CONSUMER_GROUP_ID,
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            value_deserializer=lambda v: json.loads(v.decode("utf-8"))
        )
        try:
            await self.consumer.start()
            logger.info(f"DLQ Worker successfully subscribed to topic: '{DLQ_TOPIC}' ")
        except KafkaError as e:
            logger.critical(f"Failed to connect to Kafka cluster: {e}")
            sys.exit(1)
    async def process_message(self, message):
        data = message.value 
        event_id = data.get("event_id", "UNKNOWN")
        event_type = data.get("event_type", "UNKNOWN")
        dlq_reason = data.get("dlq_reason", "No failure reason provided")
        dlq_failed_at = data.get("dlq_failed_at", "N/A")
        logger.error(
            f"[DLQ EVENT RECORDED] ID: {event_id} | Type: {event_type}| "
            f"Failed At: {dlq_failed_at} | Reason: {dlq_reason}"
        )
        DLQ_EVENTS_TOTAL.labels(event_type=event_type).inc()

    async def run(self):
        await self.start()
        try:
            async for msg in self.consumer:
                if not self.is_running:
                    break
                await self.process_message(msg)
        except asyncio.CancelledError:
            logger.info("DLQ Worker task cancelled.")
        except KafkaError as e:
            logger.error(f"Kafka error encountered during execution: {e}")
        finally:
            await self.stop()

    async def stop(self):
        logger.info("Stopping DLQ Worker and closing consumer connection...")
        self.is_running = False
        if self.consumer:
            await self.consumer.stop()
        logger.info("DLQ Worker stopped cleanly")

async def main():
    try:
        start_http_server(PROMETHEUS_PORT)
        logger.info(f"Prometheus metrics exposed on port {PROMETHEUS_PORT}")
    except Exception as e:
        logger.warning(f"Could not start Protheus server on port {PROMETHEUS_PORT}: {e}")

    worker = DLQWorker()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT,signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(worker.stop()))
    await worker.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("DLQ Worker process terminated.")