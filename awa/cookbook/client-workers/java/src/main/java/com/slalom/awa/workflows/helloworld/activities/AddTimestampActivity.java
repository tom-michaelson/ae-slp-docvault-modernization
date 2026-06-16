package com.slalom.awa.workflows.helloworld.activities;

import com.slalom.awa.workflows.helloworld.models.AddTimestampActivityInput;
import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

@ActivityInterface
public interface AddTimestampActivity {

    @ActivityMethod(name = "add-timestamp-activity")
    String run(AddTimestampActivityInput input);
}
