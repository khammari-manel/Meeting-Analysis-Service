# Message Queue Service (RabbitMQ)

This service provides a simple, robust messaging queue system based on RabbitMQ. It enables reliable communication between different components or services by publishing and consuming structured messages. The main goal is to facilitate asynchronous, decoupled data exchange for scenarios such as notifications, event processing, or workflow orchestration.

## Architecture

- **RabbitMQ Server:** The core message broker, responsible for managing queues, exchanges, and message delivery.
- **Publisher Script (`publish_test.py`):** Sends messages to the queue in a predefined format, supporting single, batch, and source-specific publishing.
- **Consumer Script (`consume_test.py`):** Listens for and processes messages from the queue, handling all notifications regardless of source.
- **Docker & Docker Compose:** Used for local development and testing, providing an isolated RabbitMQ environment with persistent storage and management UI.
- **Environment Configuration:** Credentials and settings are managed via `.env` files for flexibility and security.

## Features

- **Message Queuing:** Supports publishing and consuming structured messages with source, info, and timestamp fields.
- **Persistence:** Message data is stored in a Docker volume (`rabbitmq_data`) to ensure durability across restarts.
- **Management UI:** RabbitMQ's web interface (http://localhost:15672) allows monitoring, configuration, and troubleshooting.
- **Simple Testing Scripts:** Easy-to-use Python scripts for sending and receiving messages, suitable for development and demonstration.
- **Configurable Credentials:** Secure setup via environment variables.

## Technologies Used

- **RabbitMQ:** Open-source message broker for reliable queuing.
- **Python 3.6+:** For publisher and consumer scripts.
- **Docker & Docker Compose:** Containerization and orchestration for local development.
- **CloudAMQP:** For production/remote hosting (see below).

## Onboarding & Local Setup

### Prerequisites

- Docker and Docker Compose installed
- Python 3.6+ and pip

### Environment Configuration

1. Copy the example environment file:
   ```
   cp .env.example .env
   ```
2. Edit `.env` to set your desired RabbitMQ username and password:
   ```
   RABBITMQ_DEFAULT_USER=admin
   RABBITMQ_DEFAULT_PASS=strongpassword
   ```

### Install Python Dependencies

Install required packages:
```
pip install -r requirements.txt
```

### Running RabbitMQ Locally

Start the RabbitMQ server:
```
docker-compose up -d
```
- RabbitMQ will run in a container with management UI enabled.
- Ports exposed: `5672` (AMQP), `15672` (web UI).
- Credentials are taken from your `.env` file.

### Testing the Message Queue

**Message Format:**
```json
{
  "source": "MeetingNote or CodeAnalysis",
  "info": "Description of what has changed",
  "timestamp": 1234567890.123
}
```

**Publish messages:**
```
python publish_test.py                # Send a single random message
python publish_test.py MeetingNote    # Send a specific source type
python publish_test.py batch 5        # Send a batch of random messages
```

**Consume messages:**
```
python consume_test.py
```
- The consumer will receive all notifications.
- Stop with `CTRL+C`.

### Management Interface

Access the RabbitMQ web UI at [http://localhost:15672](http://localhost:15672) using your credentials.

### Stopping the Service

Stop RabbitMQ:
```
docker-compose down
```
Remove persistent volume:
```
docker-compose down -v
```

### Data Persistence

Message data is stored in the Docker volume `rabbitmq_data`, ensuring messages survive container restarts.

## CloudAMQP Hosting

For production or remote deployment, this service was hosted using [CloudAMQP](https://www.cloudamqp.com/), a managed RabbitMQ provider. This replaces the need for manual remote deployment and offers scalability, monitoring, and reliability out of the box.

**Note:** The local Docker setup is intended for development and testing only. For production, configure your publisher and consumer scripts to connect to your CloudAMQP instance using the provided connection details.

## Author

[@hsb-lschwartz](https://gitlab.com/hsb-lschwartz)
