#!/bin/bash

# Development environment setup script

set -e

echo "Setting up development environment for Autonomous Code Improver..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Warning: Node.js is not installed. UI components may not work properly."
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
pip install -e .

# Install development dependencies
echo "Installing development dependencies..."
pip install -e ".[dev,test]"

# Set up pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Start infrastructure services
echo "Starting infrastructure services..."
docker-compose -f infra/neo4j/docker-compose.override.yml up -d

# Wait for Neo4j to be ready
echo "Waiting for Neo4j to be ready..."
until curl -s http://localhost:7474 || echo "Waiting for Neo4j..."; do sleep 1; done

# Seed the database
echo "Seeding the database..."
./scripts/seed.sh

echo "Development environment setup complete!"
echo ""
echo "To activate the virtual environment in your current shell, run:"
echo "source venv/bin/activate"
echo ""
echo "To start the application, run:"
echo "make dev"
