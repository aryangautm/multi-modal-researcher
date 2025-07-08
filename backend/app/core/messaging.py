import asyncio

from aiokafka import AIOKafkaProducer

from .config import settings

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
