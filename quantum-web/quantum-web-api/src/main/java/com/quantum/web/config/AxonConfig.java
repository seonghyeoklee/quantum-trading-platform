package com.quantum.web.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.ComponentScan;

/**
 * Axon Framework Configuration
 * 
 * CQRS/Event Sourcing 프레임워크 설정
 * - Aggregate 및 Projection 스캔
 */
@Configuration
@ComponentScan(basePackages = {
    "com.quantum.trading.platform.command.aggregate",    // Command Side Aggregates
    "com.quantum.trading.platform.query.projection",     // Query Side Projections
    "com.quantum.trading.platform.query.service"         // Query Services
})
public class AxonConfig {
}