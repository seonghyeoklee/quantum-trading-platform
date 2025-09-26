package com.quantum.backtest.infrastructure.persistence;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * StrategyExecutionLogEntity JPA Repository
 */
@Repository
public interface JpaStrategyExecutionLogRepository extends JpaRepository<StrategyExecutionLogEntity, Long> {

    /**
     * 백테스트 ID로 전략 실행 로그 조회 (시간순 정렬)
     *
     * @param backtestId 백테스트 UUID
     * @return 전략 실행 로그 리스트
     */
    @Query("SELECT log FROM StrategyExecutionLogEntity log WHERE log.backtestId = :backtestId ORDER BY log.logTimestamp ASC, log.stepSequence ASC")
    List<StrategyExecutionLogEntity> findByBacktestIdOrderByTimestampAscStepSequenceAsc(@Param("backtestId") String backtestId);

    /**
     * 백테스트 ID와 로그 타입으로 전략 실행 로그 조회
     *
     * @param backtestId 백테스트 UUID
     * @param logType 로그 타입
     * @return 전략 실행 로그 리스트
     */
    List<StrategyExecutionLogEntity> findByBacktestIdAndLogTypeOrderByLogTimestampAscStepSequenceAsc(String backtestId, String logType);

    /**
     * 백테스트 ID로 전략 실행 로그 삭제
     *
     * @param backtestId 백테스트 UUID
     */
    void deleteByBacktestId(String backtestId);
}