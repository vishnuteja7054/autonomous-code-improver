#!/bin/bash

# Wait for services to be ready

set -e

echo "Waiting for services to be ready..."

# Wait for Neo4j
echo "Waiting for Neo4j..."
until curl -s http://localhost:7474 || echo "Waiting for Neo4j..."; do
  sleep 1
done

# Wait for PostgreSQL
echo "Waiting for PostgreSQL..."
until pg_isready -h localhost -p 5432 -U postgres; do
  sleep 1
done

# Wait for Redis
echo "Waiting for Redis..."
until redis-cli -h localhost -p 6379 ping; do
  sleep 1
done

# Wait for NATS
echo "Waiting for NATS..."
until wget --no-verbose --tries=1 --spider http://localhost:8222/jsz?acc=all&streams=0 || exit 1; do
  sleep 1
done

echo "All services are ready!"
