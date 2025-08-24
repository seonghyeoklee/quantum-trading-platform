package com.quantum.web.config;

import com.influxdb.client.InfluxDBClient;
import com.influxdb.client.InfluxDBClientFactory;
import com.influxdb.client.WriteApiBlocking;
import com.influxdb.client.QueryApi;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * InfluxDB 설정 클래스
 * 시계열 데이터베이스 연결 및 클라이언트 빈 생성
 */
@Configuration
public class InfluxDBConfig {

    @Value("${influxdb.url}")
    private String url;

    @Value("${influxdb.token}")
    private String token;

    @Value("${influxdb.org}")
    private String org;

    @Value("${influxdb.bucket}")
    private String bucket;

    @Bean
    public InfluxDBClient influxDBClient() {
        return InfluxDBClientFactory.create(url, token.toCharArray(), org, bucket);
    }

    @Bean
    public WriteApiBlocking writeApiBlocking(InfluxDBClient client) {
        return client.getWriteApiBlocking();
    }

    @Bean
    public QueryApi queryApi(InfluxDBClient client) {
        return client.getQueryApi();
    }

    // Configuration getters
    public String getUrl() {
        return url;
    }

    public String getToken() {
        return token;
    }

    public String getOrg() {
        return org;
    }

    public String getBucket() {
        return bucket;
    }
}