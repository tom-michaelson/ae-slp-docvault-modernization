package com.slalom.awa.workflows.helloworld.models;

public class HelloWorldWorkflowInput {
    private String name;

    public HelloWorldWorkflowInput() {
    }

    public HelloWorldWorkflowInput(String name) {
        this.name = name;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }
}
