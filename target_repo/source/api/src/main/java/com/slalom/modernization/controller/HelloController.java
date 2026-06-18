package com.slalom.modernization.controller;

import org.springframework.cache.annotation.Cacheable;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class HelloController {

    @GetMapping("/hello")
    @Cacheable(value = "greetings", key = "#name")
    public String hello(@RequestParam(defaultValue = "world") String name) {
        return "Hello, " + name + "!";
    }
}
