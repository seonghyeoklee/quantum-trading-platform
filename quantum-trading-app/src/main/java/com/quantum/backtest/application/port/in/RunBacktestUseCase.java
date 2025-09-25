package com.quantum.backtest.application.port.in;

import com.quantum.backtest.domain.BacktestConfig;
import com.quantum.backtest.domain.BacktestId;

/**
 * 백테스팅 실행 Use Case
 */
public interface RunBacktestUseCase {

    /**
     * 새로운 백테스팅을 실행한다.
     * @param config 백테스팅 설정
     * @return 백테스팅 ID
     */
    BacktestId runBacktest(BacktestConfig config);
}