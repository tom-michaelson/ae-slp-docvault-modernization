package com.slalom.awa.workflows.helloworld.activities;

import com.slalom.awa.workflows.helloworld.models.AddTimestampActivityInput;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class AddTimestampActivityImpl implements AddTimestampActivity {

    @Override
    public String run(AddTimestampActivityInput input) {
        String timestamp = LocalDateTime.now()
                .format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

        return String.format(input.getFormat(), input.getInput(), timestamp);
    }
}
