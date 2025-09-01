package com.quantum.web.repository;

import com.quantum.web.entity.UserTradingSettings;
import com.quantum.web.dto.TradingConfigDto;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 사용자 트레이딩 설정 리포지토리
 */
@Repository
public interface UserTradingSettingsRepository extends JpaRepository<UserTradingSettings, Long> {

    /**
     * 사용자 ID로 트레이딩 설정 조회
     */
    Optional<UserTradingSettings> findByUserId(String userId);

    /**
     * 트레이딩 모드별 사용자 수 조회
     */
    @Query("SELECT COUNT(u) FROM UserTradingSettings u WHERE u.tradingMode = :tradingMode")
    long countByTradingMode(@Param("tradingMode") TradingConfigDto.TradingMode tradingMode);

    /**
     * 자동매매 활성화된 사용자 목록 조회
     */
    List<UserTradingSettings> findByAutoTradingEnabledTrue();

    /**
     * 실전투자 모드 사용자 목록 조회
     */
    @Query("SELECT u FROM UserTradingSettings u WHERE u.tradingMode = 'PRODUCTION'")
    List<UserTradingSettings> findProductionModeUsers();

    /**
     * 특정 기간 이후 업데이트된 설정 조회
     */
    @Query("SELECT u FROM UserTradingSettings u WHERE u.updatedAt >= :since")
    List<UserTradingSettings> findUpdatedSince(@Param("since") LocalDateTime since);

    /**
     * 키움 계좌 ID로 설정 조회
     */
    Optional<UserTradingSettings> findByKiwoomAccountId(String kiwoomAccountId);

    /**
     * 리스크 레벨별 사용자 수 조회
     */
    @Query("SELECT u.riskLevel, COUNT(u) FROM UserTradingSettings u GROUP BY u.riskLevel")
    List<Object[]> countByRiskLevel();

    /**
     * 사용자 존재 여부 확인
     */
    boolean existsByUserId(String userId);
}