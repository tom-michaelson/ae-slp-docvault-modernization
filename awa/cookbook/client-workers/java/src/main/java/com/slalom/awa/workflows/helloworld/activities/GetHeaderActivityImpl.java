package com.slalom.awa.workflows.helloworld.activities;

public class GetHeaderActivityImpl implements GetHeaderActivity {

    @Override
    public String run() {
        return "#########################\n" +
               "##  Hello From Java!   ##\n" +
               "#########################\n" +
               "\n";
    }
}
