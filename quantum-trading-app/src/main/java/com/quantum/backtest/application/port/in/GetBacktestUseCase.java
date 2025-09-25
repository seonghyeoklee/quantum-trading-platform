package com.quantum.backtest.application.port.in;

import com.quantum.backtest.domain.Backtest;
import com.quantum.backtest.domain.BacktestId;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.Optional;

/**
 * 백테스팅 조회 Use Case
 */
public interface GetBacktestUseCase {

    /**
     * 백테스팅 ID로 조회한다.
     * @param id 백테스팅 ID
     * @return 백테스팅 (Optional)
     */
    Optional<Backtest> getBacktest(BacktestId id);

    /**
     * 모든 백테스팅 목록을 페이징으로 조회한다.
     * @param pageable 페이징 정보
     * @return 백테스팅 페이지
     */
    Page<Backtest> getAllBacktests(Pageable pageable);

    /**
     * 백테스팅 상세 정보를 조회한다. (거래 내역 포함)
     * @param id 백테스팅 ID
     * @return 백테스팅 상세 (Optional)
     */
    Optional<Backtest> getBacktestDetail(BacktestId id);
}