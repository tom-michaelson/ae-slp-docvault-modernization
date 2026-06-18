# Cross-platform Makefile for Java client worker
# Works on Windows (with GNU Make), Linux, and macOS

# Detect the operating system
ifeq ($(OS),Windows_NT)
    DETECTED_OS := Windows
    GRADLE := gradlew.bat
    RM := del /Q
    RMDIR := rmdir /S /Q
else
    DETECTED_OS := $(shell uname -s)
    GRADLE := ./gradlew
    RM := rm -f
    RMDIR := rm -rf
endif

# Default target
.DEFAULT_GOAL := worker

# Phony targets (targets that don't represent files)
.PHONY: help install worker clean test build

help:
	@echo "Available commands:"
	@echo "  install       Install dependencies and setup Gradle wrapper"
	@echo "  worker        Run the Java worker"
	@echo "  build         Build the project"
	@echo "  test          Run tests"
	@echo "  clean         Clean build artifacts"
	@echo "  help          Show this help message"
	@echo ""
	@echo "Detected OS: $(DETECTED_OS)"

install:
	@echo "Setting up Gradle wrapper..."
	@gradle wrapper --gradle-version=8.5
	@echo "Installing dependencies..."
	@$(GRADLE) build
	@echo "Installation complete!"

worker:
	@echo "Starting Java worker..."
	@$(GRADLE) run

build:
	@echo "Building project..."
	@$(GRADLE) build

test:
	@echo "Running tests..."
	@$(GRADLE) test

clean:
	@echo "Cleaning project..."
	@$(GRADLE) clean
	@echo "Clean finished."
