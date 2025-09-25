package com.quantum.backtest.application.port.out;

import com.quantum.backtest.domain.Backtest;
import com.quantum.backtest.domain.BacktestId;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;

import java.util.Optional;

/**
 * 백테스팅 Repository Port
 */
public interface BacktestRepositoryPort {

    /**
     * 백테스팅을 저장한다.
     * @param backtest 백테스팅
     * @return 저장된 백테스팅
     */
    Backtest save(Backtest backtest);

    /**
     * 백테스팅 ID로 조회한다.
     * @param id 백테스팅 ID
     * @return 백테스팅 (Optional)
     */
    Optional<Backtest> findById(BacktestId id);

    /**
     * 모든 백테스팅을 페이징으로 조회한다.
     * @param pageable 페이징 정보
     * @return 백테스팅 페이지
     */
    Page<Backtest> findAll(Pageable pageable);

    /**
     * 백테스팅을 삭제한다.
     * @param id 백테스팅 ID
     */
    void deleteById(BacktestId id);

    /**
     * 백테스팅 존재 여부를 확인한다.
     * @param id 백테스팅 ID
     * @return 존재 여부
     */
    boolean existsById(BacktestId id);
}