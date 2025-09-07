# ADR 0001: Assumptions and Defaults

## Status

Accepted

## Context

This document captures the assumptions and default choices made during the design and implementation of the Autonomous Code Improvement system.

## Assumptions

### Primary Languages

- **Assumption**: The system will primarily support Python and TypeScript.
- **Rationale**: These are among the most popular programming languages and have good tooling support for parsing and analysis.
- **Implications**: Other languages can be added in the future by extending the parsing and analysis modules.

### Runtime Environment

- **Assumption**: The system will run on Linux/x86_64 with Ubuntu 22.04.
- **Rationale**: Linux is the dominant platform for server applications and development tools.
- **Implications**: The system may not work on other platforms without modifications.

### Package Managers

- **Assumption**: Python projects will use pip and uv, while TypeScript projects will use pnpm.
- **Rationale**: These are modern and efficient package managers for their respective ecosystems.
- **Implications**: Projects using other package managers may not be fully supported.

### Containerization

- **Assumption**: The system will use Docker and Docker Compose for containerization.
- **Rationale**: Docker provides consistent environments and simplifies deployment.
- **Implications**: The system requires Docker to be installed and configured.

### Databases

- **Assumption**: Neo4j will be used for the knowledge graph, and PostgreSQL for metadata and results.
- **Rationale**: Neo4j is optimized for graph-based data models, while PostgreSQL is a reliable relational database.
- **Implications**: The system requires these databases to be installed and configured.

### Caching

- **Assumption**: Redis will be used for caching.
- **Rationale**: Redis is a fast in-memory data store that is well-suited for caching.
- **Implications**: The system requires Redis to be installed and configured.

### Message Bus

- **Assumption**: NATS will be used as the message bus.
- **Rationale**: NATS is lightweight, fast, and simple to use for inter-service communication.
- **Implications**: The system requires NATS to be installed and configured.

### CI/CD

- **Assumption**: GitHub Actions will be used for continuous integration and deployment.
- **Rationale**: GitHub Actions integrates well with GitHub repositories and provides a generous free tier.
- **Implications**: The system is designed to work with GitHub Actions, but other CI/CD systems could be used with modifications.

### VCS Host

- **Assumption**: GitHub will be the primary VCS host.
- **Rationale**: GitHub is the most popular code hosting platform and provides a rich API.
- **Implications**: Other VCS hosts like GitLab or Bitbucket could be supported with additional implementation.

### License

- **Assumption**: The system will be licensed under Apache 2.0.
- **Rationale**: Apache 2.0 is a permissive license that allows for both open source and commercial use.
- **Implications**: The system can be used in a wide variety of projects without licensing restrictions.

### LLM Endpoint

- **Assumption**: The system will use ChatGLM as the LLM endpoint via HTTP.
- **Rationale**: ChatGLM provides good performance for code-related tasks and can be self-hosted.
- **Implications**: Other LLM providers could be supported by modifying the LLM client.

### Execution Sandbox

- **Assumption**: The system will use Docker-in-Docker with seccomp for sandboxing untrusted code.
- **Rationale**: Docker provides strong isolation, and seccomp adds an additional layer of security.
- **Implications**: The system requires Docker to be configured for DinD.

## Defaults

### File Size Limit

- **Default**: Maximum file size of 10MB for analysis.
- **Rationale**: Large files can significantly slow down analysis and may not be practical to process.
- **Configuration**: Can be adjusted via the `max_file_size_mb` environment variable.

### Timeout

- **Default**: 300 seconds (5 minutes) for analysis operations.
- **Rationale**: Provides a reasonable balance between allowing complex analysis and preventing indefinite hangs.
- **Configuration**: Can be adjusted via the `timeout_seconds` environment variable.

### Log Level

- **Default**: INFO.
- **Rationale**: Provides a good balance between verbosity and performance.
- **Configuration**: Can be adjusted via the `LOG_LEVEL` environment variable.

### Telemetry

- **Default**: Enabled.
- **Rationale**: Telemetry data helps improve the system over time.
- **Configuration**: Can be disabled via the `enable_telemetry` environment variable.

## Consequences

These assumptions and defaults have the following consequences:

1. The system is optimized for Python and TypeScript projects, with support for other languages requiring additional work.
2. The system is designed to run on Linux and may require modifications for other platforms.
3. The system requires several external dependencies (Neo4j, PostgreSQL, Redis, NATS, Docker) to be installed and configured.
4. The system is designed to integrate with GitHub and GitHub Actions, but could be adapted for other platforms.
5. The system includes telemetry by default, which can be disabled for privacy or performance reasons.

## Future Considerations

1. Support for additional programming languages could be added by extending the parsing and analysis modules.
2. Support for other platforms (Windows, macOS) could be added with platform-specific modifications.
3. Alternative databases, message buses, or LLM providers could be supported with additional implementation.
4. The telemetry system could be enhanced to provide more detailed insights while respecting privacy.

## Decision

We accept these assumptions and defaults as the foundation for the Autonomous Code Improvement system. They provide a clear direction for development while allowing for future flexibility and expansion.
