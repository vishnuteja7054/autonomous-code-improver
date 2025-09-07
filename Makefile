.PHONY: help install install-dev test test-unit test-integration test-e2e lint format type-check security-check build clean run dev docker-build docker-run docker-clean release

help:
    @echo "Available commands:"
    @echo "  install      Install the package and dependencies"
    @echo "  install-dev  Install development dependencies"
    @echo "  test         Run all tests"
    @echo "  test-unit    Run unit tests"
    @echo "  test-integration Run integration tests"
    @echo "  test-e2e     Run end-to-end tests"
    @echo "  lint         Run code linting with ruff"
    @echo "  format       Format code with black and isort"
    @echo "  type-check   Run type checking with mypy"
    @echo "  security-check Run security checks with bandit and safety"
    @echo "  build        Build the package"
    @echo "  clean        Clean build artifacts"
    @echo "  run          Run the application"
    @echo "  dev          Run the application in development mode"
    @echo "  docker-build Build Docker images"
    @echo "  docker-run   Run the application with Docker"
    @echo "  docker-clean Clean Docker resources"
    @echo "  release      Create a new release"

install:
    pip install -e .

install-dev:
    pip install -e ".[dev,test]"
    pre-commit install

test:
    pytest

test-unit:
    pytest -m "not integration and not e2e"

test-integration:
    pytest -m "integration"

test-e2e:
    pytest -m "e2e"

lint:
    ruff check agent/
    ruff check --fix agent/

format:
    black agent/
    isort agent/

type-check:
    mypy agent/

security-check:
    bandit -r agent/
    safety check

build:
    python -m build

clean:
    rm -rf build/
    rm -rf dist/
    rm -rf *.egg-info/
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete

run:
    uvicorn agent.runtime.orchestrator:app --reload

dev:
    uvicorn agent.runtime.orchestrator:app --reload --host 0.0.0.0 --port 8000

docker-build:
    docker build -t autonomous-code-improver .

docker-run:
    docker run -it --rm -p 8000:8000 autonomous-code-improver

docker-clean:
    docker system prune -f

release: clean build
    @echo "Release version $(VERSION)"
    git tag -a v$(VERSION) -m "Release v$(VERSION)"
    git push origin v$(VERSION)
