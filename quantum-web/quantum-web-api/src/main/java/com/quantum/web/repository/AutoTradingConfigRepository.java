package com.quantum.web.repository;

import com.quantum.web.entity.AutoTradingConfig;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 자동매매 설정 Repository
 *
 * 자동매매 설정 엔티티에 대한 데이터 액세스를 담당
 */
@Repository
public interface AutoTradingConfigRepository extends JpaRepository<AutoTradingConfig, String> {

    /**
     * 활성화 상태별 설정 조회
     *
     * @param isActive 활성화 여부
     * @return 활성화 상태에 맞는 설정 목록
     */
    List<AutoTradingConfig> findByIsActive(Boolean isActive);

    /**
     * 전략명별 설정 조회
     *
     * @param strategyName 전략명
     * @return 해당 전략의 설정 목록
     */
    List<AutoTradingConfig> findByStrategyName(String strategyName);

    /**
     * 종목별 설정 조회
     *
     * @param symbol 종목 코드
     * @return 해당 종목의 설정 목록
     */
    List<AutoTradingConfig> findBySymbol(String symbol);

    /**
     * 종목별 활성화된 설정 조회
     *
     * @param symbol 종목 코드
     * @param isActive 활성화 여부
     * @return 종목의 활성화된 설정 목록
     */
    List<AutoTradingConfig> findBySymbolAndIsActive(String symbol, Boolean isActive);

    /**
     * 전략명과 종목으로 활성화된 설정 존재 여부 확인
     *
     * @param strategyName 전략명
     * @param symbol 종목 코드
     * @param isActive 활성화 여부
     * @return 존재 여부
     */
    boolean existsByStrategyNameAndSymbolAndIsActive(String strategyName, String symbol, Boolean isActive);

    /**
     * 전략명과 종목으로 설정 조회
     *
     * @param strategyName 전략명
     * @param symbol 종목 코드
     * @return 해당 조건의 설정 목록
     */
    List<AutoTradingConfig> findByStrategyNameAndSymbol(String strategyName, String symbol);

    /**
     * 생성일 범위로 설정 조회
     *
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 생성일 범위에 해당하는 설정 목록
     */
    List<AutoTradingConfig> findByCreatedAtBetween(LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 최근 생성된 설정 조회 (생성일 기준 내림차순)
     *
     * @param limit 조회 개수
     * @return 최근 생성된 설정 목록
     */
    @Query("SELECT c FROM AutoTradingConfig c ORDER BY c.createdAt DESC LIMIT :limit")
    List<AutoTradingConfig> findRecentConfigs(@Param("limit") int limit);

    /**
     * 활성화된 설정 중 특정 전략명을 가진 설정 조회
     *
     * @param strategyName 전략명
     * @return 활성화된 해당 전략의 설정 목록
     */
    @Query("SELECT c FROM AutoTradingConfig c WHERE c.strategyName = :strategyName AND c.isActive = true")
    List<AutoTradingConfig> findActiveConfigsByStrategy(@Param("strategyName") String strategyName);

    /**
     * 특정 자본금 범위의 설정 조회
     *
     * @param minCapital 최소 자본금
     * @param maxCapital 최대 자본금
     * @return 자본금 범위에 해당하는 설정 목록
     */
    @Query("SELECT c FROM AutoTradingConfig c WHERE c.capital BETWEEN :minCapital AND :maxCapital")
    List<AutoTradingConfig> findByCapitalRange(@Param("minCapital") java.math.BigDecimal minCapital, 
                                               @Param("maxCapital") java.math.BigDecimal maxCapital);

    /**
     * 특정 리스크 레벨 범위의 설정 조회
     *
     * @param maxStopLoss 최대 손절 비율
     * @return 손절 비율이 지정된 값 이하인 설정 목록
     */
    @Query("SELECT c FROM AutoTradingConfig c WHERE c.stopLossPercent <= :maxStopLoss AND c.isActive = true")
    List<AutoTradingConfig> findLowRiskConfigs(@Param("maxStopLoss") java.math.BigDecimal maxStopLoss);

    /**
     * 특정 종목의 활성화된 설정 개수 조회
     *
     * @param symbol 종목 코드
     * @return 활성화된 설정 개수
     */
    @Query("SELECT COUNT(c) FROM AutoTradingConfig c WHERE c.symbol = :symbol AND c.isActive = true")
    long countActiveConfigsBySymbol(@Param("symbol") String symbol);

    /**
     * 전체 활성화된 설정 개수 조회
     *
     * @return 전체 활성화된 설정 개수
     */
    long countByIsActive(Boolean isActive);

    /**
     * 특정 기간 동안 생성된 설정 개수 조회
     *
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 기간 내 생성된 설정 개수
     */
    long countByCreatedAtBetween(LocalDateTime startDate, LocalDateTime endDate);

    /**
     * 전략별 설정 통계 조회
     *
     * @return 전략별 설정 개수와 평균 자본금
     */
    @Query("SELECT c.strategyName, COUNT(c), AVG(c.capital) FROM AutoTradingConfig c GROUP BY c.strategyName")
    List<Object[]> findStrategyStatistics();

    /**
     * 종목별 활성화된 설정과 총 자본금 조회
     *
     * @return 종목별 활성화된 설정 개수와 총 자본금
     */
    @Query("SELECT c.symbol, COUNT(c), SUM(c.capital) FROM AutoTradingConfig c WHERE c.isActive = true GROUP BY c.symbol")
    List<Object[]> findActiveSymbolStatistics();

    /**
     * ID로 활성화된 설정 조회
     *
     * @param id 설정 ID
     * @return 활성화된 설정 (Optional)
     */
    Optional<AutoTradingConfig> findByIdAndIsActive(String id, Boolean isActive);

    /**
     * 설정 소프트 삭제 (비활성화)
     *
     * @param id 설정 ID
     */
    @Query("UPDATE AutoTradingConfig c SET c.isActive = false, c.updatedAt = CURRENT_TIMESTAMP WHERE c.id = :id")
    void softDeleteById(@Param("id") String id);

    /**
     * 전략명으로 모든 설정 비활성화
     *
     * @param strategyName 전략명
     */
    @Query("UPDATE AutoTradingConfig c SET c.isActive = false, c.updatedAt = CURRENT_TIMESTAMP WHERE c.strategyName = :strategyName")
    void deactivateByStrategy(@Param("strategyName") String strategyName);
}