# Payment Processing Service

A backend payment processing system built with FastAPI, PostgreSQL, and RabbitMQ, implementing an Outbox pattern and asynchronous event-driven architecture for reliable payment delivery and processing.
The system supports creating payments, persisting them in a relational database, and reliably publishing events to RabbitMQ for downstream processing (consumer + webhook delivery).

## Core Features


1. Payment API
- Create payments via REST API `POST /api/payments`
- Retrieve payment details `GET /api/payments/{id}`
- Idempotency support to prevent duplicate payments

2. Outbox Pattern
- Reliable event publishing using a PostgreSQL outbox table
- Transactions ensure consistency between:
  - payment creation
  - outbox event insertion
- Background worker publishes events to RabbitMQ

3. Event-Driven Architecture
- RabbitMQ-based messaging system
- Exchanges:
  - payments (main flow)
  - payments.retry (retry flow with TTL)
  - payments.dlq (dead-letter queue)
- Automatic retry mechanism using queue TTL + dead-letter routing
4. Consumer Worker
- Processes payment.created events asynchronously
- Simulates payment processing (success/failure)
- Updates payment status in PostgreSQL
- Sends webhook notifications on completion
- Routes failed messages to retry or DLQ

5. Webhook Delivery
- Async webhook delivery with retries and exponential backoff
- Configurable timeout and retry attempts
- Failure-safe error handling
---

## Running the Project with Docker Compose

### Quick Start

1. **Clone the repository**:
   ```bash
   git https://github.com/yooshark/t-mkkl-payment-processing.git
   cd t-mkkl-payment-processing
   ```

2. **Create `.env.prod` file** (see environment variables section above or `.env.example`)

3. **Build and start all services:**
   ```bash
   docker compose up --build
   ```

---

## Local Development Setup

If you prefer to run the application without Docker:

1. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv

   # On Windows:
   .venv\Scripts\activate

   # On Linux/Mac:
   source .venv/bin/activate
   ```

2. **Install dependencies:**

   Using `uv` (recommended):
   ```bash
   uv sync
   ```

3. **Configure environment**:
   Create a `.env` file and set your local PostgreSQL credentials (see `.env.example`).

4. **Run migrations**:
   ```bash
   alembic -c alembic.ini upgrade head
   ```

5. **Start the server**:
   ```bash
   uv run src/run.py
   ```

---

**Access the service:**
   - API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/api/docs` (only for DEBUG mode)

---

### Useful Commands

```bash
# View logs
docker compose logs -f api

# Stop all services
docker compose down

# Stop and remove volumes (clean database)
docker compose down -v

# Rebuild specific service
docker compose build api
```
