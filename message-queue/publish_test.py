# Script to send test messages to RabbitMQ

import pika
import json
import sys
import time
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Connection parameters
credentials = pika.PlainCredentials(
    os.getenv('RABBITMQ_DEFAULT_USER', 'admin'),
    os.getenv('RABBITMQ_DEFAULT_PASS', 'strongpassword')
)
parameters = pika.ConnectionParameters(
    host='localhost',
    port=5672,
    credentials=credentials
)

# Connect to RabbitMQ
connection = pika.BlockingConnection(parameters)
channel = connection.channel()

# Define exchange and queue
exchange_name = 'notifications'
queue_name = 'notification_queue'

# Create exchange and queue, bind them
channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)
channel.queue_declare(queue=queue_name, durable=True)
channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key='notification.*')

# Message source types
source_types = ['MeetingNote', 'CodeAnalysis']

def publish_message(source_type=None):
    if source_type is None:
        source_type = random.choice(source_types)

    # Create sample message
    message = {
        'source': source_type,
        'info': f'xyz{random.randint(1000, 9999)} has changed',
        'timestamp': time.time()
    }

    # Create routing key based on source type
    routing_key = f'notification.{source_type.lower()}'

    # Publish message
    channel.basic_publish(
        exchange=exchange_name,
        routing_key=routing_key,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
            content_type='application/json'
        )
    )

    print(f"Published message: {json.dumps(message)} with routing key: {routing_key}")

if __name__ == "__main__":
    # Check if source type is provided as command line argument
    if len(sys.argv) > 1 and sys.argv[1] in source_types:
        source_type = sys.argv[1]
        publish_message(source_type)
    elif len(sys.argv) > 1 and sys.argv[1] == 'batch':
        # Send a batch of messages
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        print(f"Publishing {count} messages...")
        for _ in range(count):
            publish_message()
    else:
        # Send a single random message
        publish_message()

    # Close connection
    connection.close()
    print("Connection closed")
