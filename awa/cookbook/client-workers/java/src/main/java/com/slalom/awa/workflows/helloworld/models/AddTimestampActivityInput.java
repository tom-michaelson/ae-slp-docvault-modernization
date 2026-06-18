package com.slalom.awa.workflows.helloworld.models;

public class AddTimestampActivityInput {
    private String input;
    private String format;

    public AddTimestampActivityInput() {
    }

    public AddTimestampActivityInput(String input, String format) {
        this.input = input;
        this.format = format;
    }

    public String getInput() {
        return input;
    }

    public void setInput(String input) {
        this.input = input;
    }

    public String getFormat() {
        return format;
    }

    public void setFormat(String format) {
        this.format = format;
    }
}
