package com.slalom.awa.configuration;

public class TemporalConfiguration {
    private final String clientTargetHost;
    private final String clientNamespace;
    private final String taskQueue;

    public TemporalConfiguration() {
        this("localhost:7233", "default", "awa_client_java");
    }

    public TemporalConfiguration(String clientTargetHost, String clientNamespace, String taskQueue) {
        this.clientTargetHost = clientTargetHost;
        this.clientNamespace = clientNamespace;
        this.taskQueue = taskQueue;
    }

    public String getClientTargetHost() {
        return clientTargetHost;
    }

    public String getClientNamespace() {
        return clientNamespace;
    }

    public String getTaskQueue() {
        return taskQueue;
    }
}
