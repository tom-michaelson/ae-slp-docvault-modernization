# AWA Client Worker Starter - Java

This is a starter project for building with the [Slalom Agentic Workflow Accelerator (AWA)](https://bitbucket.org/slalom-consulting/agentic-workflow-accelerator). This starter project is located in the main AWA repository at `cookbook/client-workers/java/`.

## Overview

AWA supports polyglot deployments. This means that you can build your workflows in any language you want (leveraging shared child workflows and activities within AWA core) and then use AWA to run them.

![AWA Polyglot Deployment](./../../docs/images/awa-polyglot-architecture.png)

## CRITICAL

To get VS Code (or whatever IDE you're using) to work nicely, it's important that you open the `cookbook/client-workers/java` directory itself rather than the root directory of the repo. This will ensure your environment tooling works properly.

### Project Structure

```
client-workers/java/
├── build.gradle                          # Gradle build configuration
├── settings.gradle                       # Gradle settings
├── Makefile                              # Build automation
├── src/
│   └── main/
│       ├── java/
│       │   └── com/slalom/awa/
│       │       ├── App.java              # Application entry point
│       │       ├── configuration/        # Configuration classes
│       │       ├── converters/           # Custom Temporal payload converters
│       │       └── workflows/
│       │           └── helloworld/       # Sample workflow implementation
│       │               ├── HelloWorldWorkflow.java      # Workflow interface
│       │               ├── HelloWorldWorkflowImpl.java  # Workflow implementation
│       │               ├── activities/                  # Workflow activities
│       │               │   ├── AddTimestampActivity.java
│       │               │   ├── AddTimestampActivityImpl.java
│       │               │   ├── GetHeaderActivity.java
│       │               │   └── GetHeaderActivityImpl.java
│       │               └── models/                      # Data models
│       │                   ├── AddTimestampActivityInput.java
│       │                   └── HelloWorldWorkflowInput.java
│       └── resources/
│           ├── application.properties    # Application configuration
│           └── logback.xml              # Logging configuration
```

## Prerequisites

- Java 11 or higher
- Gradle 8.5 or higher (optional - the wrapper will be installed)

## Run

### 1. Run AWA via the AWA CLI

```bash
# From the root of the AWA repo
make start
```

OR

```bash
# From the root of the AWA repo
uv run -m awa.main start
```

### 2. Run the Java worker (this app)

```bash
# From the `cookbook/client-workers/java` directory
make worker
```

OR

```bash
# From the `cookbook/client-workers/java` directory
./gradlew run
```

### 3. Run the workflow via the AWA CLI

```bash
# From the root of the AWA repo
uv run -m awa.main run -w hello-world-java -i "{'name': 'World'}" -q awa_client_java
```

## Build and Install

```bash
# Install dependencies and setup Gradle wrapper
make install

# Build the project
make build

# Run tests
make test

# Clean build artifacts
make clean
```

## Debug

You can debug your client worker like any other Java application. Open the project in your IDE of choice (IntelliJ IDEA, Eclipse, VS Code with Java extensions), then use standard debugging features.

For IntelliJ IDEA:
1. Open the `cookbook/client-workers/java` directory as a project
2. Set breakpoints in your code
3. Run the `App` class in debug mode

For VS Code:
1. Install the Java Extension Pack
2. Open the `cookbook/client-workers/java` directory
3. Use the Run and Debug view to start debugging

## Configuration

Configuration is managed through `src/main/resources/application.properties`:

```properties
# Temporal Configuration
temporal.client.targetHost=localhost:7233
temporal.client.namespace=default
temporal.taskQueue=awa_client_java
```

You can override these values using system properties:

```bash
./gradlew run -Dtemporal.client.targetHost=temporal.example.com:7233
```

## Test

Automated tests are critical for maintaining quality in any application. A major benefit of using Temporal is that workflows and activities are just functions, which makes testing them easy.

See the [Temporal Java SDK docs](https://docs.temporal.io/develop/java/testing-suite) for details on testing.

## Extending the Worker

To add new workflows:

1. Create a new workflow interface with `@WorkflowInterface` annotation
2. Create the implementation class
3. Register it in `App.java` using `worker.registerWorkflowImplementationTypes()`

To add new activities:

1. Create a new activity interface with `@ActivityInterface` annotation
2. Create the implementation class
3. Register it in `App.java` using `worker.registerActivitiesImplementations()`

## Dependencies

This project uses:
- Temporal Java SDK for workflow orchestration
- Jackson for JSON serialization
- Logback for logging
- JUnit 5 for testing
