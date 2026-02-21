import pika
import json
import os

def send_to_queue(events):
    cloudamqp_url = os.getenv("CLOUDAMQP_URL")
    if not cloudamqp_url:
        print("No CLOUDAMQP_URL configured")
        return
    try:
        params = pika.URLParameters(cloudamqp_url)
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.exchange_declare(
            exchange='notification',
            exchange_type='topic',
            durable=True
        )
        for event in events:
            channel.basic_publish(
                exchange='notification',
                routing_key='analysis.meeting-notes',
                body=json.dumps(event),
                properties=pika.BasicProperties(delivery_mode=2)
            )
        connection.close()
        print(f"Sent {len(events)} events to queue")
    except Exception as e:
        print(f"Error sending to queue: {e}")