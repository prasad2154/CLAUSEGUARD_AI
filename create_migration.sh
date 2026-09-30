#!/bin/bash
# Generate the initial Alembic migration after starting docker-compose

echo "Starting Docker containers..."
docker-compose up -d postgres qdrant

echo "Waiting for PostgreSQL to be ready..."
sleep 5

echo "Generating initial migration..."
docker-compose run --rm backend alembic revision --autogenerate -m "Initial migration"

echo "Applying migration..."
docker-compose run --rm backend alembic upgrade head

echo "Database migrations complete!"
