# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**dev-start** is a Python-based technology configurator for developers. It automates the setup of development environments by:
- **Verifying and installing Git** if not present
- Cloning Git repositories
- Auto-detecting technologies (Java/SpringBoot, Python, Node.js)
- Installing and configuring necessary tools and dependencies
- Supporting corporate proxy configurations
- Creating environment files and project configurations

## Architecture

### Core Components

1. **CLI (src/cli.py)** - Main interface using Click framework
2. **Detector (src/detector.py)** - Technology detection from repository files
3. **Installers (src/installers/)** - Technology-specific installation logic
   - Base installer with common functionality (download, command execution)
   - Git installer (MinGit for Windows)
   - Java/SpringBoot installer (JDK, Maven/Gradle)
   - Python installer (virtualenv, pip)
   - Node.js installer (npm)
4. **Managers**
   - ProxyManager: HTTP/HTTPS proxy configuration
   - RepositoryManager: Git operations
   - EnvironmentManager: .env files and system paths

### Design Patterns

- **Strategy Pattern**: Different installers for different technologies
- **Template Method**: BaseInstaller defines common installation flow
- **Separation of Concerns**: Each module has a single responsibility

## Development Commands

### Run Application
```bash
# Development mode
python -m src.cli <repo-urls>

# With proxy
python -m src.cli --http-proxy http://proxy:8080 --https-proxy http://proxy:8080 <repo-urls>
```

### Build Windows Executable
```bash
# Using build script
build.bat

# Manual build
pip install -r requirements.txt
pyinstaller dev-start.spec --clean
```

### Run Tests
```bash
# Run all tests (46 tests total)
python -m unittest discover tests -v

# Run specific test modules
python -m unittest tests.test_detector         # 4 tests
python -m unittest tests.test_proxy_manager    # 7 tests
python -m unittest tests.test_env_manager      # 7 tests
python -m unittest tests.test_installers       # 14 tests
python -m unittest tests.test_repo_manager     # 6 tests
python -m unittest tests.test_integration      # 8 tests
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Key Implementation Details

### Technology Detection
- Files checked: pom.xml, build.gradle, requirements.txt, package.json, etc.
- Indicators: Content-based detection for SpringBoot projects
- Default versions: Java 17, Python 3.11, Node.js 20.11.0

### Security Considerations
- Downloads only from official sources
- Proxy support for corporate environments
- No credential storage in code
- Environment variables for sensitive data

### Output Location
All projects are cloned to: `%USERPROFILE%/dev-start-projects/`
Tools are installed to: `%USERPROFILE%/.dev-start/tools/`

## Test Coverage

The application has comprehensive test coverage with 46 automated tests:

- **Unit Tests**: Testing individual components (detector, managers, installers)
- **Integration Tests**: Testing component interactions and workflows
- **Mock-based Tests**: For external dependencies (Git operations, downloads)

All tests use temporary directories and proper cleanup to ensure isolation.

## Development Principles

### Code Quality and Architecture
1. **Clean Architecture** - Maintain clear separation of concerns and dependency rules
2. **Performance Based on Big O Notation** - Analyze and optimize algorithmic complexity
3. **Mitigated Against Main CVEs** - Address common security vulnerabilities proactively
4. **Service Resilience and Cache Usage** - Build fault-tolerant services with appropriate caching strategies
5. **Modern Design Based on Context** - Apply contemporary design patterns appropriate to the use case
6. **Functionality Guarantee Through Testing Pyramid** - Ensure comprehensive test coverage across unit, integration, and E2E tests
7. **Security** - Apply security best practices throughout the codebase
8. **Observability** - Implement logging, metrics, and tracing for system visibility
9. **Design System Principles** - Maintain consistency in UI/UX components and patterns
10. **Construction by Phases and SubPhases** - Break down implementation into manageable incremental steps
11. **Documented Changes** - Maintain clear documentation of all modifications
12. **Application Changes with Functional Build** - Ensure builds remain functional after each change

## Agent Guidelines

When working in this repository:

1. **Token Economy** - Focus on implementation over summaries; be concise and action-oriented
