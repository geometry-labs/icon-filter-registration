<p align="center">
  <h3 align="center">ICON Filter Registration API</h3>

  <p align="center">
    The registration API microservice for <a href="https://github.com/geometry-labs/icon-api">icon-api</a>.
    <br />
</p>

## Getting Started

### Docker Build

To build container for production:

```bash
docker build --target prod -t icon-filter-registration .
```

To build container for development/testing:

```bash
docker build --target test -t icon-filter-registration .
```

## Usage

Docker container can be used either as a standalone worker or in a docker-compose stack.
To use in a standalone configuration:

```bash
docker run icon-filter-registration
```

Or in a docker-compose stack:

```yaml
registration:
image: geometrylabs/icon-filter-registration:latest
hostname: registration
ports:
  - 8008:80
environment:
  REGISTRATION_KAFKA_SERVER: kafka:9092
  REGISTRATION_SCHEMA_SERVER: http://schemaregistry:8081
  REGISTRATION_POSTGRES_SERVER: postgres
  REGISTRATION_POSTGRES_USER: postgres
  REGISTRATION_POSTGRES_PASSWORD: password
```

Just be sure to set the corresponding environment variables to suit your configuration.

### Environment Variables

| Variable                 | Default             | Description                                     |
|--------------------------|---------------------|-------------------------------------------------|
| API_ENDPOINT_PREFIX      | /api/v1             | Prefix for the API                              |
| DOCS_ENDPOINT_PREFIX     | /api/v1/docs        | Prefix for the API docs                         |
| KAFKA_SERVER             |                     | URL for Kafka server                            |
| SCHEMA_SERVER            |                     | URL for Schema Registry server                  |
| KAFKA_COMPRESSION        | gzip                | Kafka compression type                          |
| REGISTRATIONS_TOPIC      | event_registrations | Kafka topic for registration messages           |
| BROADCASTER_EVENTS_TOPIC | broadcaster_events  | Kafka topic for broadcaster event messages      |
| POSTGRES_SERVER          |                     | Postgres server hostname                        |
| POSTGRES_PORT            | 5432                | Postgres server port                            |
| POSTGRES_USER            |                     | Postgres username                               |
| POSTGRES_PASSWORD        |                     | Postgres password                               |
| POSTGRES_DATABASE        | postgres            | Postgres database name                          |
| MAX_CONFIRM_WAIT         | 10                  | Number of retries for registration confirmation |

### Registration
#### Broadcaster
POST: _/broadcaster/register_

```json
{
    "connection_type": "ws",
    "endpoint": "wss://test",
    "event_ids": [
      "1234-1234-1234"
    ],
    "transaction_events": [
        {
            "to_address": "cx0000000000000000000000000000000000000000",
            "from_address": "cx0000000000000000000000000000000000000001"
        }
    ],
    "log_events": [
        {
            "address": "cx0000000000000000000000000000000000000001",
            "keyword": "LogKeyword",
            "position": 1
        }
    ]
}
```

#### Log Event
POST: _/logevent/register_

```json
{
    "address": "cx0000000000000000000000000000000000000001",
    "keyword": "LogKeyword",
    "position": 1
}
```

#### Transaction
POST: _/transaction/register_

```json
{
    "to_address": "cx0000000000000000000000000000000000000000",
    "from_address": "cx0000000000000000000000000000000000000001"
}
```

### Unregister
#### Broadcaster
POST: _/broadcaster/unregister_

```json
{
    "broadcaster_id": "1234-1234-1234"
}
```

#### Log Event
POST: _/logevent/unregister_

```json
{
    "reg_id": "1234-1234-1234",
    "address": "cx0000000000000000000000000000000000000001",
    "keyword": "LogKeyword",
    "position": 1
}
```

#### Transaction
POST: _/transaction/unregister_

```json
{
    "reg_id": "1234-1234-1234",
    "to_address": "cx0000000000000000000000000000000000000000",
    "from_address": "cx0000000000000000000000000000000000000001"
}
```

## License

Distributed under the Apache 2.0 License. See `LICENSE` for more information.
