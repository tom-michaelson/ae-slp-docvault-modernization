package com.slalom.awa.converters;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.PropertyNamingStrategies;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import io.temporal.common.converter.JacksonJsonPayloadConverter;

public class CamelCasePayloadConverter extends JacksonJsonPayloadConverter {

    public CamelCasePayloadConverter() {
        super(createObjectMapper());
    }

    private static ObjectMapper createObjectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        mapper.setPropertyNamingStrategy(PropertyNamingStrategies.LOWER_CAMEL_CASE);
        mapper.registerModule(new JavaTimeModule());
        return mapper;
    }
}
