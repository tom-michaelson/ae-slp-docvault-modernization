# Cross-platform Makefile
# Works on Windows (with GNU Make), Linux, and macOS

# Detect the operating system
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    PYTHON := python
    RM := del /Q
    RMDIR := rmdir /S /Q
else
    DETECTED_OS := $(shell uname -s)
    PYTHON := python3
    RM := rm -f
    RMDIR := rm -rf
endif

# Default target
.DEFAULT_GOAL := install

# Variables
PYTEST_ARGS := -v

# Phony targets (targets that don't represent files)
.PHONY: help test test-verbose test-coverage generate-api-tests test-api install lint lint-fix format pre-commit pre-commit-all check all clean docs ui baml start stop stop-all verify-deps docker-build docker-up docker-down docker-logs run-docker start-terminate test-ui test-ui-headed test-ui-debug generate-typescript-models ai-rules-generate ai-rules-clean

# Help target - displays available commands
help:
	@echo "Available commands:"
	@echo "  make          Install dependencies (default)"
	@echo "  verify-deps   Verify all required dependencies are installed"
	@echo "  start         Start all AWA services"
	@echo "  start-detach  Start all AWA services in detached mode"
	@echo "  stop          Stop all AWA services"
	@echo "  stop-all      Aggressively stop all AWA services including orphaned processes"
	@echo "  start-terminate Start all AWA services and terminate all workflows"
	@echo "  clean-start   Fresh start. Clean, then install, then start."
	@echo "  run           Run the application (API, Temporal)"
	@echo "  mcp           Run the MCP server"
	@echo "  test          Run unit tests with pytest"
	@echo "  test-verbose  Run unit tests with verbose output"
	@echo "  test-coverage Run unit tests with coverage report"
	@echo "  generate-api-tests Generate API tests from OpenAPI specification"
	@echo "  test-api      Run API tests"
	@echo "  test-workflow Run workflow integration tests (must manually start/stop services)"
	@echo "  test-workflow-verbose Run workflow tests with verbose output (must manually start/stop services)"
	@echo "  run-test-workflow Run workflow integration tests (services automatically start/stop)"
	@echo "  run-test-workflow-verbose Run workflow tests with verbose output (services automatically start/stop)"
	@echo "  test-all      Run all tests (unit + api + workflow)"
	@echo "  test-ui       Run Playwright UI tests"
	@echo "  test-ui-headed Run Playwright UI tests in headed mode"
	@echo "  test-ui-debug Run Playwright UI tests in debug mode"
	@echo "  lint          Run linting checks (Ruff)"
	@echo "  lint-fix      Run linting checks (Ruff) and run fixes if available"
	@echo "  format        Format code (Ruff)"
	@echo "  pre-commit    Run pre-commit hooks on staged files"
	@echo "  pre-commit-all Run pre-commit hooks on all files"
	@echo "  clean         Remove temporary files and build artifacts"
	@echo "  ai-rules-generate Generate AI rule files"
	@echo "  ai-rules-clean Clean generated AI rule files"
	@echo "  ci            Run CI using Dagger"
	@echo "  ci-workflow-tests Run CI workflow tests using Dagger"
	@echo "  ci-publish-sdk Publish SDK using Dagger"
	@echo "  help          Show this help message"
	@echo ""
	@echo "Docker commands:"
	@echo "  docker-build  Build all Docker images"
	@echo "  docker-build-api     Build the AWA API Docker image"
	@echo "  docker-build-ui     Build the AWA UI Docker image"
	@echo "  docker-up     Start services with docker compose"
	@echo "  docker-down   Stop and remove containers"
	@echo "  docker-logs   View service logs"
	@echo "  start-docker    Main command for running with Docker"
	@echo "  start-docker-supporting  Main command for running with Docker (supporting only)"
	@echo ""
	@echo "Detected OS: $(DETECTED_OS)"

# Test target - runs pytest with verbose
test:
	uv run -m pytest $(PYTEST_ARGS) tests/unit

# Test with extra verbose output
test-verbose:
	uv run -m pytest -vv tests/unit

# Test with coverage
test-coverage:
	uv run -m pytest --cov --cov-report=term-missing $(PYTEST_ARGS) tests/unit

# Generate API tests from OpenAPI specification
generate-api-tests:
	uv run python -m tests.api.generation.generate_api_tests

# Run API tests
test-api:
	uv run -m pytest $(PYTEST_ARGS) tests/api

# Run all tests in tests/workflow directory with automatic service handling
run-test-workflow:
	uv run -m awa.main start -d -s temporal_worker,temporal_server
	uv run -m pytest -s $(PYTEST_ARGS) tests/workflow/tests
	uv run -m awa.main stop

# Run workflow tests with verbose output with automatic service handling
run-test-workflow-verbose:
	uv run -m awa.main start -d -s temporal_worker,temporal_server
	uv run -m pytest -vv -s $(PYTEST_ARGS) tests/workflow/tests
	uv run -m awa.main stop

# Run all tests in tests/workflow directory (must manually start / stop)
test-workflow:
	uv run -m awa.main status -s temporal_server,temporal_worker || (echo "Temporal services are not running. Aborting tests." && exit 1)
	uv run -m pytest -s $(PYTEST_ARGS) tests/workflow/tests

# Run workflow tests with verbose output (must manually start / stop)
test-workflow-verbose:
	uv run -m awa.main status -s temporal_server,temporal_worker || (echo "Temporal services are not running. Aborting tests." && exit 1)
	uv run -m pytest -vv -s $(PYTEST_ARGS) tests/workflow/tests

# Run all tests (unit + api + workflow)
test-all: test test-api test-workflow

# Playwright UI tests
test-ui:
	cd tests/ui && npx playwright test --reporter=list

# Playwright UI tests with HTML report
test-ui-report:
	cd tests/ui && npx playwright test --reporter=html

# Playwright UI tests in headed mode
test-ui-headed:
	cd tests/ui && npx playwright test --headed

# Playwright UI tests in debug mode
test-ui-debug:
	cd tests/ui && npx playwright test --debug

# Install dependencies
install: base-install docs-prep

base-install: verify-deps
	uv sync
	pnpm install
	@echo "Installing UI dependencies..."
	npx copyfiles .env ui
	cd ui && pnpm install
ifeq ($(OS),Windows_NT)
	@python -c "import sys,os,pathlib;p=pathlib.Path('.venv/pyvenv.cfg');p.write_text(f'home = {sys.prefix}\ninclude-system-site-packages = false\nversion = {sys.version.split()[0]}\nexecutable = {sys.executable}\ncommand = {sys.executable} -m venv {os.path.abspath(\".venv\")}\n',encoding='utf-8') if not p.exists() else None"
endif
	uv run pre-commit install
	uv run -m scripts.setup_config
	uv run -m scripts.clear_registry
	uv run -m scripts.generate_baml_client

# Generate BAML client
baml:
	uv run -m scripts.generate_baml_client

# Lint code
lint:
	uv run ruff check

lint-fix:
	uv run ruff check --fix

# Format code
format:
	uv run ruff format

# Run pre-commit hooks
pre-commit:
	uv run pre-commit run

# Run pre-commit hooks on all files
pre-commit-all:
	uv run pre-commit run --all-files

# Start all services
start:
	uv run -m awa.main start

# Start all services
start-detach:
	uv run -m awa.main start --detach

# Stop all services
stop:
ifeq ($(OS),Windows_NT)
	-@powershell -Command "if (Test-Path '.venv') { try { uv run -m awa.main stop-all } catch { Write-Host 'Stop command failed, continuing...' } } else { Write-Host 'No virtual environment found, skipping stop command' }"
else
	-@if [ -d .venv ]; then uv run -m awa.main stop 2>/dev/null || true; else echo "No virtual environment found, skipping stop command"; fi
endif

# Aggressively stop all AWA services including orphaned processes
stop-all:
	uv run -m awa.main stop-all

# Start all services and terminate all workflows
start-terminate: baml
	uv run -m awa.main start -t

# Run application
run: baml
	uv run -m awa.main run

# Run AWA MCP server
mcp:
	uv run -m awa.main mcp

# Clean project
clean: stop ai-rules-clean
	@echo "Cleaning project..."
ifeq ($(OS),Windows_NT)
	-@powershell -Command "try { if (Test-Path '.venv') { Remove-Item -Path '.venv' -Recurse -Force } } catch { } ; exit 0" 2>nul
	-@powershell -Command "try { if (Test-Path 'logs') { Remove-Item -Path 'logs' -Recurse -Force } } catch { } ; exit 0" 2>nul
	-@powershell -Command "try { Get-ChildItem -Path . -Recurse -Directory -Name '.cache', '__pycache__', 'node_modules', '_copied', '_dynamic', 'baml_dynamic' -ErrorAction SilentlyContinue | ForEach-Object { if (Test-Path $$_) { Remove-Item -Path $$_ -Recurse -Force -ErrorAction SilentlyContinue } } } catch { } ; exit 0" 2>nul
	-@powershell -Command "try { Get-ChildItem -Path . -Recurse -File -Filter '*.pyc' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue } catch { } ; exit 0" 2>nul
	-@powershell -Command "try { Get-ChildItem -Path . -Recurse -File -Filter '*.db' -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue } catch { } ; exit 0" 2>nul
else
	-$(RMDIR) .venv
	-$(RMDIR) logs
endif
ifeq ($(OS),Windows_NT)
	@echo "Additional cleanup completed (cache directories and temp files)"
else
	@find . -type d -name ".cache" -exec $(RMDIR) {} +
	@find . -type d -name "__pycache__" -exec $(RMDIR) {} +
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "node_modules" -exec $(RMDIR) {} +
	@find . -type d -name "_copied" -exec $(RMDIR) {} +
	@find . -type d -name "_dynamic" -exec $(RMDIR) {} +
	@find . -type d -name "baml_dynamic" -exec $(RMDIR) {} +
	@find . -type f -name "*.db" -delete
	@touch pyproject.toml
endif
	@echo "Clean finished."

clean-start: clean install start
start-clean: clean install start

# Run docs site
# region make-docs
# Cookbook docs now in repository permanently
docs-prep:
	pnpm install
	uv run -m scripts.generate_api_reference_docs
	uv run python scripts/ai-documentation-generator/tools/generate_multi_rules.py generate

docs: docs-prep
	pnpm run docs:dev
# endregion make-docs

docs-dev: docs-prep
	pnpm run docs:dev

docs-build: docs-prep
	pnpm run docs:build

docs-preview: docs-build
	pnpm run docs:preview

# Run AWA UI
ui: generate-typescript-models
	uv run -m awa.main ui

# Docker commands
docker-build:
	@echo "Preparing Docker build context..."
	@echo "Building Docker images..."
	docker compose build

docker-up:
	@echo "Starting Docker services..."
	docker compose up -d

docker-up-build:
	@echo "Preparing Docker build context..."
	@echo "Building Docker images and starting services..."
	docker compose up -d --build

docker-build-up: docker-up-build

docker-up-supporting:
	@echo "Starting Docker services..."
	docker compose -f docker-compose.awa-supporting.yml up -d

docker-down:
	@echo "Stopping Docker services..."
	docker compose down

docker-logs:
	@echo "Showing Docker service logs..."
	docker compose logs -f

docker-build-api:
	docker compose build api

docker-build-ui:
	@echo "Preparing Docker build context..."
	docker compose build ui

echo-docker:
	@echo "AWA and supporting services are running in Docker!"
	@echo "AWA UI: http://localhost:$${AWA_UI_PORT:-8000}"
	@echo "AWA API: http://localhost:$${AWA_API_PORT:-8001}/docs"
	@echo "Temporal UI: http://localhost:$${TEMPORAL_UI_PORT:-8002}"
	@echo "PostgreSQL: localhost:$${POSTGRES_DEFAULT_PORT:-5432}"

echo-docker-supporting-intro:
	@echo "AWA supporting services are running in Docker!"

echo-docker-supporting:
	@echo "Langfuse: http://localhost:3001"
	@echo "LiteLLM: http://localhost:4002"
	@echo ""
	@echo "Use 'make docker-logs' to view logs"
	@echo "Use 'make docker-down' to stop services"

start-docker: docker-build docker-up echo-docker echo-docker-supporting
	@echo ""

start-docker-supporting: docker-up-supporting echo-docker-supporting-intro echo-docker-supporting
	@echo ""

ci:
	dagger run --verbose uv run pipelines/ci.py

ci-workflow-tests:
	dagger run --verbose uv run pipelines/ci.py workflow-tests

ci-publish-sdk:
	dagger run --verbose uv run -m pipelines.publish_sdk

verify-deps:
ifeq ($(DETECTED_OS),Windows)
	powershell -ExecutionPolicy Bypass -File scripts/verify_install_prerequisites.ps1
else
	bash scripts/verify_install_prerequisites.sh
endif

generate-typescript-models:
	uv run -m scripts.generate_typescript_models

# AI Rules management
ai-rules-generate:
	@echo "Generating AI rule files..."
	uv run python scripts/ai-documentation-generator/tools/generate_multi_rules.py generate

ai-rules-clean:
	@echo "Cleaning generated AI rule files..."
ifeq ($(OS),Windows_NT)
	-@powershell -Command "if (Test-Path '.venv') { try { uv run python scripts/ai-documentation-generator/tools/generate_multi_rules.py clean } catch { Write-Host 'AI rules clean failed, continuing...' } } else { Write-Host 'No virtual environment found, skipping ai-rules-clean' }"
else
	-@if [ -d .venv ]; then uv run python scripts/ai-documentation-generator/tools/generate_multi_rules.py clean 2>/dev/null || true; else echo "No virtual environment found, skipping ai-rules-clean"; fi
endif
