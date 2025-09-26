package com.quantum.backtest.domain.strategy;

import com.quantum.backtest.domain.BacktestResult;
import com.quantum.backtest.domain.PriceData;
import com.quantum.backtest.domain.StrategyType;

import java.util.List;

/**
 * 거래 전략 인터페이스
 * 모든 거래 전략은 이 인터페이스를 구현해야 함 (Strategy Pattern)
 */
public interface TradingStrategy {

    /**
     * 이 전략이 지원하는 전략 타입을 반환
     */
    StrategyType getStrategyType();

    /**
     * 전략을 실행하여 백테스팅 결과를 생성
     *
     * @param context 전략 실행에 필요한 컨텍스트 정보
     * @param priceHistory 주가 데이터 히스토리
     * @return 백테스팅 실행 결과
     */
    BacktestResult execute(StrategyContext context, List<PriceData> priceHistory);

    /**
     * 전략의 이름을 반환
     */
    default String getName() {
        return getStrategyType().getDisplayName();
    }

    /**
     * 전략의 설명을 반환
     */
    default String getDescription() {
        return getStrategyType().getDescription();
    }
}