import pika
import json

exchange_name = 'notifications'
routing_key = 'notification.meetingnote'
queue_name = 'notification_queue'

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

# Exchange deklarieren (Typ 'topic' oder 'direct', je nachdem was dein Publisher nutzt)
channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)

# Queue deklarieren
channel.queue_declare(queue=queue_name, durable=True)

# Queue an Exchange binden
channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)

# Callback
def callback(ch, method, properties, body):
    message = json.loads(body)
    print("📥 Empfangene Nachricht:")
    print(json.dumps(message, indent=2))

channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)

print(f"📡 Warte auf Nachrichten in der Queue '{queue_name}'. Beende mit STRG+C.")
channel.start_consuming()
