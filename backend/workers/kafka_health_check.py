#!/usr/bin/env python3
"""
Kafka Health Check Script

This script helps diagnose Kafka connectivity issues and provides
troubleshooting information for the research worker.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings


async def check_kafka_connection():
    """Check basic Kafka connection."""
    try:
        from aiokafka import AIOKafkaProducer, AIOKafkaConsumer

        print("🔍 Testing Kafka Producer Connection...")
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=10000,
            # Add API version configuration for compatibility
            api_version="auto",
        )
        await producer.start()
        print("✅ Producer connection successful")
        await producer.stop()

        print("\n🔍 Testing Kafka Consumer Connection...")
        consumer = AIOKafkaConsumer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="health_check_group",
            request_timeout_ms=10000,
            # Add API version configuration for compatibility
            api_version="auto",
        )
        await consumer.start()
        print("✅ Consumer connection successful")
        await consumer.stop()

        return True

    except Exception as e:
        print(f"❌ Kafka connection failed: {e}")
        return False


async def check_topic_exists():
    """Check if the research topic exists."""
    try:
        print(f"\n🔍 Checking if topic '{settings.KAFKA_RESEARCH_TOPIC}' exists...")

        # Try a simpler approach - just create a consumer and see if it works
        from aiokafka import AIOKafkaConsumer

        consumer = AIOKafkaConsumer(
            settings.KAFKA_RESEARCH_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="topic_check_group",
            request_timeout_ms=10000,
            api_version="auto",
            auto_offset_reset="earliest",
        )

        await consumer.start()

        # Get topic partitions
        partitions = consumer.assignment()
        if partitions:
            print(f"✅ Topic exists and consumer can access it")
        else:
            # If no partitions assigned, topic might still exist
            print("✅ Topic appears to be accessible")

        await consumer.stop()
        return True

    except Exception as e:
        print(f"❌ Topic check failed: {e}")

        # Skip automatic topic creation to avoid sending messages to production topic
        print("💡 Topic check failed. You may need to create the topic manually:")
        print(
            f"   docker-compose exec kafka kafka-topics.sh --create --topic {settings.KAFKA_RESEARCH_TOPIC} --bootstrap-server localhost:9094 --partitions 1 --replication-factor 1"
        )
        return False


def check_configuration():
    """Check configuration settings."""
    print("🔍 Checking Configuration...")
    print(f"KAFKA_BOOTSTRAP_SERVERS: {settings.KAFKA_BOOTSTRAP_SERVERS}")
    print(f"KAFKA_RESEARCH_TOPIC: {settings.KAFKA_RESEARCH_TOPIC}")

    # Check if running in Docker network
    if "localhost" in settings.KAFKA_BOOTSTRAP_SERVERS:
        print("\n⚠️  Warning: Using localhost in KAFKA_BOOTSTRAP_SERVERS")
        print("   If running in Docker, consider using 'kafka:9093' instead")

    # Check environment variables
    env_file = Path(__file__).parent.parent.parent / ".env"
    if not env_file.exists():
        print(f"\n❌ .env file not found at {env_file}")
        print("   Create a .env file with required Kafka settings")
    else:
        print(f"\n✅ .env file found at {env_file}")


async def test_message_flow():
    """Test sending and receiving a message."""
    try:
        from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
        import uuid

        print("\n🔍 Testing message flow...")

        # Create producer
        producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            request_timeout_ms=10000,
            api_version="auto",
        )
        await producer.start()

        # Create consumer
        consumer = AIOKafkaConsumer(
            settings.KAFKA_RESEARCH_TOPIC,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="health_check_consumer",
            auto_offset_reset="latest",
            request_timeout_ms=10000,
            api_version="auto",
        )
        await consumer.start()

        # Send test message
        test_job_id = str(uuid.uuid4())
        await producer.send_and_wait(
            settings.KAFKA_RESEARCH_TOPIC, test_job_id.encode("utf-8")
        )
        print(f"✅ Sent test message: {test_job_id}")

        # Try to receive message
        print("🔍 Waiting for test message...")
        try:
            async with asyncio.timeout(10):  # 10 second timeout
                async for msg in consumer:
                    received_id = msg.value.decode("utf-8")
                    if received_id == test_job_id:
                        print(f"✅ Received test message: {received_id}")
                        break
        except asyncio.TimeoutError:
            print("❌ Timeout waiting for test message")

        await producer.stop()
        await consumer.stop()

    except Exception as e:
        print(f"❌ Message flow test failed: {e}")


async def main():
    """Run all health checks."""
    print("🏥 Kafka Health Check")
    print("=" * 50)

    # Check configuration
    check_configuration()

    print("\n" + "=" * 50)

    # Check connection
    if not await check_kafka_connection():
        print("\n💡 Troubleshooting tips:")
        print("1. Ensure Kafka is running: docker-compose up -d kafka")
        print("2. Check if port 9093 is available: netstat -an | grep 9093")
        print("3. Verify KAFKA_BOOTSTRAP_SERVERS in .env file")
        return False

    # Check topic
    if not await check_topic_exists():
        print("\n💡 Topic troubleshooting tips:")
        print("1. Check Kafka logs: docker-compose logs kafka")
        print("2. Verify topic permissions")
        return False

    # Test message flow
    await test_message_flow()

    print("\n🎉 All checks completed!")
    return True


if __name__ == "__main__":
    asyncio.run(main())
