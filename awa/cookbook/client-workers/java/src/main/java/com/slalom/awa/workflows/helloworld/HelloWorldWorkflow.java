package com.slalom.awa.workflows.helloworld;

import com.slalom.awa.workflows.helloworld.models.HelloWorldWorkflowInput;
import io.temporal.workflow.WorkflowInterface;
import io.temporal.workflow.WorkflowMethod;

@WorkflowInterface
public interface HelloWorldWorkflow {

    @WorkflowMethod(name = "hello-world-java")
    String run(HelloWorldWorkflowInput input);
}
