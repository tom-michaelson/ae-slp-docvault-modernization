package com.slalom.awa;

import com.slalom.awa.configuration.TemporalConfiguration;
import com.slalom.awa.converters.CamelCasePayloadConverter;
import com.slalom.awa.workflows.helloworld.HelloWorldWorkflow;
import com.slalom.awa.workflows.helloworld.HelloWorldWorkflowImpl;
import com.slalom.awa.workflows.helloworld.activities.AddTimestampActivity;
import com.slalom.awa.workflows.helloworld.activities.AddTimestampActivityImpl;
import com.slalom.awa.workflows.helloworld.activities.GetHeaderActivity;
import com.slalom.awa.workflows.helloworld.activities.GetHeaderActivityImpl;
import io.temporal.client.WorkflowClient;
import io.temporal.client.WorkflowClientOptions;
import io.temporal.common.converter.DefaultDataConverter;
import io.temporal.serviceclient.WorkflowServiceStubs;
import io.temporal.worker.Worker;
import io.temporal.worker.WorkerFactory;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.io.InputStream;
import java.util.Properties;

public class App {
    private static final Logger log = LoggerFactory.getLogger(App.class);

    public static void main(String[] args) {
        TemporalConfiguration config = loadConfiguration();

        log.info("Starting AWA Java Worker...");
        log.info("Connecting to Temporal at: {}", config.getClientTargetHost());
        log.info("Namespace: {}", config.getClientNamespace());
        log.info("Task Queue: {}", config.getTaskQueue());

        // Create service stubs
        WorkflowServiceStubs service = WorkflowServiceStubs.newServiceStubs(
                io.temporal.serviceclient.WorkflowServiceStubsOptions.newBuilder()
                        .setTarget(config.getClientTargetHost())
                        .build());

        // Create workflow client with custom data converter
        WorkflowClient client = WorkflowClient.newInstance(
                service,
                WorkflowClientOptions.newBuilder()
                        .setNamespace(config.getClientNamespace())
                        .setDataConverter(DefaultDataConverter.newDefaultInstance()
                                .withPayloadConverterOverrides(new CamelCasePayloadConverter()))
                        .build());

        // Create worker factory
        WorkerFactory factory = WorkerFactory.newInstance(client);

        // Create worker
        Worker worker = factory.newWorker(config.getTaskQueue());

        // Register workflow implementation
        worker.registerWorkflowImplementationTypes(HelloWorldWorkflowImpl.class);

        // Register activities
        worker.registerActivitiesImplementations(
                new AddTimestampActivityImpl(),
                new GetHeaderActivityImpl());

        // Start worker
        factory.start();

        log.info("Worker started successfully and listening on task queue: {}", config.getTaskQueue());

        // Keep the main thread alive
        try {
            Thread.currentThread().join();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("Worker interrupted", e);
        }
    }

    private static TemporalConfiguration loadConfiguration() {
        Properties props = new Properties();
        try (InputStream input = App.class.getClassLoader().getResourceAsStream("application.properties")) {
            if (input == null) {
                log.warn("Unable to find application.properties, using default configuration");
                return new TemporalConfiguration();
            }
            props.load(input);
        } catch (IOException e) {
            log.error("Error loading configuration", e);
            return new TemporalConfiguration();
        }

        return new TemporalConfiguration(
                props.getProperty("temporal.client.targetHost", "localhost:7233"),
                props.getProperty("temporal.client.namespace", "default"),
                props.getProperty("temporal.taskQueue", "awa_client_java")
        );
    }
}
