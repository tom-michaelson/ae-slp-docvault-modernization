package com.slalom.awa.workflows.helloworld.activities;

import io.temporal.activity.ActivityInterface;
import io.temporal.activity.ActivityMethod;

@ActivityInterface
public interface GetHeaderActivity {

    @ActivityMethod(name = "get-header-activity")
    String run();
}
