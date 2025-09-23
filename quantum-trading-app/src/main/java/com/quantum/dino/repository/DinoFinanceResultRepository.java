package com.quantum.dino.repository;

import com.quantum.dino.domain.DinoFinanceResultEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

/**
 * DINO 재무 분석 결과 리포지토리
 *
 * H2 데이터베이스와의 데이터 접근을 담당
 */
@Repository
public interface DinoFinanceResultRepository extends JpaRepository<DinoFinanceResultEntity, Long> {

    /**
     * 종목코드로 최근 분석 결과 조회 (최신 순)
     */
    List<DinoFinanceResultEntity> findByStockCodeOrderByAnalysisDateDesc(String stockCode);

    /**
     * 종목코드와 분석일로 분석 결과 존재 여부 확인
     */
    @Query("SELECT COUNT(d) > 0 FROM DinoFinanceResultEntity d " +
           "WHERE d.stockCode = :stockCode " +
           "AND DATE(d.analysisDate) = :analysisDate")
    boolean existsByStockCodeAndAnalysisDate(@Param("stockCode") String stockCode,
                                           @Param("analysisDate") LocalDate analysisDate);

    /**
     * 종목코드의 당일 분석 결과 조회
     */
    @Query("SELECT d FROM DinoFinanceResultEntity d " +
           "WHERE d.stockCode = :stockCode " +
           "AND DATE(d.analysisDate) = :analysisDate")
    Optional<DinoFinanceResultEntity> findByStockCodeAndAnalysisDate(@Param("stockCode") String stockCode,
                                                                   @Param("analysisDate") LocalDate analysisDate);

    /**
     * 특정 날짜의 모든 분석 결과 조회
     */
    @Query("SELECT d FROM DinoFinanceResultEntity d " +
           "WHERE DATE(d.analysisDate) = :analysisDate " +
           "ORDER BY d.totalScore DESC, d.stockCode ASC")
    List<DinoFinanceResultEntity> findByAnalysisDateOrderByTotalScoreDesc(@Param("analysisDate") LocalDate analysisDate);

    /**
     * 최근 N일간의 분석 결과 조회
     */
    @Query("SELECT d FROM DinoFinanceResultEntity d " +
           "WHERE d.analysisDate >= :fromDate " +
           "ORDER BY d.analysisDate DESC, d.totalScore DESC")
    List<DinoFinanceResultEntity> findRecentAnalysis(@Param("fromDate") LocalDate fromDate);

    /**
     * 총점별 종목 수 통계
     */
    @Query("SELECT d.totalScore as score, COUNT(d) as count " +
           "FROM DinoFinanceResultEntity d " +
           "WHERE DATE(d.analysisDate) = :analysisDate " +
           "GROUP BY d.totalScore " +
           "ORDER BY d.totalScore DESC")
    List<ScoreStatistics> getScoreStatistics(@Param("analysisDate") LocalDate analysisDate);

    /**
     * 총점 상위 종목 조회
     */
    @Query("SELECT d FROM DinoFinanceResultEntity d " +
           "WHERE d.totalScore >= :minScore " +
           "AND DATE(d.analysisDate) = :analysisDate " +
           "ORDER BY d.totalScore DESC, d.stockCode ASC")
    List<DinoFinanceResultEntity> findTopScoreStocks(@Param("minScore") Integer minScore,
                                                    @Param("analysisDate") LocalDate analysisDate);

    /**
     * 점수 통계 인터페이스
     */
    interface ScoreStatistics {
        Integer getScore();
        Long getCount();
    }
}