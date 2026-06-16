package com.slalom.awa.workflows.helloworld;

import com.slalom.awa.workflows.helloworld.activities.AddTimestampActivity;
import com.slalom.awa.workflows.helloworld.activities.GetHeaderActivity;
import com.slalom.awa.workflows.helloworld.models.AddTimestampActivityInput;
import com.slalom.awa.workflows.helloworld.models.HelloWorldWorkflowInput;
import io.temporal.activity.ActivityOptions;
import io.temporal.workflow.ActivityStub;
import io.temporal.workflow.Workflow;
import org.slf4j.Logger;

import java.time.Duration;

public class HelloWorldWorkflowImpl implements HelloWorldWorkflow {
    private static final Logger log = Workflow.getLogger(HelloWorldWorkflowImpl.class);

    private final GetHeaderActivity getHeaderActivity =
            Workflow.newActivityStub(GetHeaderActivity.class,
                    ActivityOptions.newBuilder()
                            .setStartToCloseTimeout(Duration.ofMinutes(1))
                            .build());

    private final AddTimestampActivity addTimestampActivity =
            Workflow.newActivityStub(AddTimestampActivity.class,
                    ActivityOptions.newBuilder()
                            .setStartToCloseTimeout(Duration.ofMinutes(1))
                            .build());

    @Override
    public String run(HelloWorldWorkflowInput input) {
        log.info("Hello from a Java workflow!");

        // Get header from local activity
        String headerResult = getHeaderActivity.run();

        // Call AWA Python-based activity
        ActivityOptions awaPythonActivityOptions = ActivityOptions.newBuilder()
                .setStartToCloseTimeout(Duration.ofMinutes(1))
                .setTaskQueue("awa_default")
                .build();

        ActivityStub untypedActivity =
                Workflow.newUntypedActivityStub(awaPythonActivityOptions);

        String helloResult = untypedActivity.execute(
                "awa-say-hello", String.class, input.getName());

        // Add timestamp to the result
        String format = headerResult + "{0}\nat {1}";
        AddTimestampActivityInput timestampInput =
                new AddTimestampActivityInput(helloResult, format);

        return addTimestampActivity.run(timestampInput);
    }
}
