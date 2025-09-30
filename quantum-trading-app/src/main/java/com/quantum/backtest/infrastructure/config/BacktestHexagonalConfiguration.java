package com.quantum.backtest.infrastructure.config;

import com.quantum.backtest.application.port.out.BacktestRepositoryPort;
import com.quantum.backtest.application.port.out.MarketDataPort;
import com.quantum.backtest.infrastructure.adapter.out.market.MockMarketDataAdapter;
import com.quantum.backtest.infrastructure.adapter.out.persistence.BacktestRepository;
import com.quantum.backtest.infrastructure.persistence.JpaBacktestRepository;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 백테스팅 모듈의 헥사고날 아키텍처 Bean 설정
 * 포트와 어댑터 간의 의존성 주입을 설정
 */
@Configuration
public class BacktestHexagonalConfiguration {

    /**
     * 시장 데이터 포트 구현체 빈 등록
     * TODO: 실제 KIS API 어댑터로 교체
     */
    @Bean
    public MarketDataPort marketDataPort() {
        return new MockMarketDataAdapter();
    }

    // BacktestRepository는 @Repository 어노테이션으로 자동 빈 등록됨
    // 따라서 별도 빈 정의 불필요
}