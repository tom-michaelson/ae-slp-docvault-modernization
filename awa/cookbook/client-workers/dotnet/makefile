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
.DEFAULT_GOAL := starter-dotnet

# Variables
PYTEST_ARGS := -v

# Phony targets (targets that don't represent files)
.PHONY: help starter-dotnet

help:
	@echo "Available commands:"
	@echo "  starter-dotnet Run the starter dotnet worker"
	@echo "  help          Show this help message"
	@echo ""
	@echo "Detected OS: $(DETECTED_OS)"

starter-dotnet:
	dotnet run --project AgenticWorkflowApp.Console/AgenticWorkflowApp.Console.csproj

clean:
	@echo "Cleaning project..."
	@find . -type d -name "bin" -exec $(RMDIR) {} +
	@find . -type d -name "obj" -exec $(RMDIR) {} +
	@touch pyproject.toml
	@echo "Clean finished."
