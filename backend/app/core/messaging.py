import asyncio
import logging

from aiokafka import AIOKafkaProducer
from models.session import ResearchJob
from schemas.research import JobStatusUpdate

from .config import settings

logger = logging.getLogger(__name__)

kafka_producer: AIOKafkaProducer | None = None


async def initialize_kafka_producer():
    """
    Initializes and starts the AIOKafkaProducer.
    This should be called during application startup.
    """
    global kafka_producer
    print("Initializing Kafka producer...")
    try:
        kafka_producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            loop=asyncio.get_event_loop(),
        )
        await kafka_producer.start()
        print("Kafka producer started successfully.")
    except Exception as e:
        print(f"FATAL: Could not initialize Kafka producer: {e}")
        raise


async def shutdown_kafka_producer():
    """
    Stops the AIOKafkaProducer.
    This should be called during application shutdown.
    """
    global kafka_producer
    if kafka_producer:
        print("Stopping Kafka producer...")
        await kafka_producer.stop()
        print("Kafka producer stopped.")


def get_kafka_producer() -> AIOKafkaProducer:
    """
    A dependency function to get the Kafka producer instance.
    Raises an exception if the producer is not initialized.
    """
    if kafka_producer is None:
        raise Exception(
            "Kafka producer is not initialized. Ensure it's started on app startup."
        )
    return kafka_producer


async def publish_status_update(job: ResearchJob, producer: AIOKafkaProducer):
    """Publishes the current job state to a job-specific Kafka topic."""
    topic_name = f"job.updates.{job.id}"

    update_payload = JobStatusUpdate.model_validate(job).model_dump_json(by_alias=True)

    try:
        await producer.send_and_wait(topic_name, value=update_payload.encode("utf-8"))
        logging.info(
            f"Published status update to topic {topic_name}",
            extra={"job_id": str(job.id)},
        )
    except Exception as e:
        logging.error(
            f"Failed to publish status update for job {job.id}: {e}",
            extra={"job_id": str(job.id)},
        )
