package com.quantum.backtest.infrastructure.adapter.out.strategy;

import com.quantum.backtest.domain.StrategyType;
import com.quantum.backtest.domain.strategy.TradingStrategy;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 거래 전략 팩토리
 * Strategy Pattern을 구현하여 전략 타입에 따른 적절한 전략 구현체를 제공
 */
@Component
public class StrategyFactory {

    private final Map<StrategyType, TradingStrategy> strategies;

    public StrategyFactory(List<TradingStrategy> strategyList) {
        this.strategies = new HashMap<>();

        // Spring에서 주입받은 모든 TradingStrategy 구현체를 Map에 등록
        for (TradingStrategy strategy : strategyList) {
            strategies.put(strategy.getStrategyType(), strategy);
        }
    }

    /**
     * 전략 타입에 해당하는 전략 구현체를 반환
     *
     * @param strategyType 실행할 전략 타입
     * @return 해당 전략 구현체
     * @throws UnsupportedOperationException 지원하지 않는 전략 타입인 경우
     */
    public TradingStrategy getStrategy(StrategyType strategyType) {
        TradingStrategy strategy = strategies.get(strategyType);

        if (strategy == null) {
            throw new UnsupportedOperationException(
                "지원하지 않는 전략입니다: " + strategyType.getDisplayName()
            );
        }

        return strategy;
    }

    /**
     * 지원하는 모든 전략 타입 목록을 반환
     */
    public Map<StrategyType, TradingStrategy> getAllStrategies() {
        return new HashMap<>(strategies);
    }

    /**
     * 특정 전략 타입이 지원되는지 확인
     */
    public boolean isSupported(StrategyType strategyType) {
        return strategies.containsKey(strategyType);
    }
}