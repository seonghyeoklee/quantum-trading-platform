package com.quantum.core.infrastructure.config;

import com.quantum.core.infrastructure.eventsourcing.JsonEventSerializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.transaction.annotation.EnableTransactionManagement;

/** Configuration for Event Sourcing infrastructure */
@Configuration
@EnableAsync
@EnableTransactionManagement
public class EventSourcingConfiguration {

    /** Primary event serializer bean */
    @Bean
    @Primary
    public JsonEventSerializer eventSerializer() {
        return new JsonEventSerializer();
    }
}
