# Script to receive messages from RabbitMQ

import pika
import json
import sys
import time
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

# Make sure exchange and queue exist
channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)
channel.queue_declare(queue=queue_name, durable=True)

# Setup queue and binding
def setup_queue():
    # Make sure the queue exists
    channel.queue_declare(queue=queue_name, durable=True)

    # Bind to all notification sources
    channel.queue_bind(
        exchange=exchange_name,
        queue=queue_name,
        routing_key='notification.*'
    )
    print("Bound to all notification sources with routing key: notification.*")

# Message callback
def callback(ch, method, properties, body):
    message = json.loads(body)
    print("\n[x] Received message:")
    print(f"    Source: {message['source']}")
    print(f"    Info: {message['info']}")
    print(f"    Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(message['timestamp']))}")
    print(f"    Routing Key: {method.routing_key}")

    # Acknowledge message (remove from queue)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    print("[x] Done processing")

if __name__ == "__main__":
    # Setup queue and binding
    setup_queue()

    # Set up quality of service - only send one message until it's acknowledged
    channel.basic_qos(prefetch_count=1)

    # Start consuming messages
    channel.basic_consume(queue=queue_name, on_message_callback=callback)

    print(f"[*] Waiting for messages. To exit press CTRL+C")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    # Close connection
    connection.close()
