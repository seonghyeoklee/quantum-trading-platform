package com.quantum.backtest.application.port.in;

import com.quantum.backtest.domain.BacktestId;

/**
 * 백테스팅 취소 Use Case
 */
public interface CancelBacktestUseCase {

    /**
     * 백테스팅을 취소한다.
     * @param id 백테스팅 ID
     */
    void cancelBacktest(BacktestId id);
}