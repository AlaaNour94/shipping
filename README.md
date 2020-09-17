# Shipment



## Run tests

Change the database's credentials to your local database's credentials
```bash
virtualenv venv --python=python3
source venv/bin/activate
pip install -r requirements
python tests
```

## Building

we use Docker compose, this will install Redis and Postgres and seed it with some data then launch the app

```bash
docker-compose up --build
```

## Swagger


```bash
http://localhost:9000/openapi/
```

## Admin Credentials

```bash
username = zid
password = zid
```

## Simple Workflow

```bash
- Get a Token using  Admin Credentials
- Create a Developer account and A Driver account
- Login using Developer Account Credentials
- Create a subscription
- Create a shipment
- Schedule it
- Print its label
- Login using Admin account
- Assign the shipment to A Driver
- Login using Driver Account
- Change the shipment state
```
