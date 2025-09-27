package com.quantum.stock.infrastructure;

import com.quantum.stock.domain.StockMaster;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * 종목 마스터 정보 JPA Repository
 *
 * 종목 검색 기능을 위한 데이터 액세스 계층
 * 회사명, 영문명, 종목코드 기반 검색 지원
 */
@Repository
public interface StockMasterRepository extends JpaRepository<StockMaster, String> {

    /**
     * 회사명으로 종목 검색 (부분 일치)
     *
     * @param companyName 검색할 회사명 (부분 문자열)
     * @return 일치하는 종목 목록 (최대 20개)
     */
    @Query("SELECT s FROM StockMaster s WHERE s.companyName LIKE %:companyName% AND s.isActive = true ORDER BY s.companyName")
    List<StockMaster> findByCompanyNameContainingIgnoreCaseAndIsActiveTrue(@Param("companyName") String companyName);

    /**
     * 영문 회사명으로 종목 검색 (부분 일치)
     *
     * @param companyNameEn 검색할 영문 회사명 (부분 문자열)
     * @return 일치하는 종목 목록 (최대 20개)
     */
    @Query("SELECT s FROM StockMaster s WHERE s.companyNameEn LIKE %:companyNameEn% AND s.isActive = true ORDER BY s.companyNameEn")
    List<StockMaster> findByCompanyNameEnContainingIgnoreCaseAndIsActiveTrue(@Param("companyNameEn") String companyNameEn);

    /**
     * 종목코드로 종목 검색 (부분 일치)
     *
     * @param stockCode 검색할 종목코드 (부분 문자열)
     * @return 일치하는 종목 목록 (최대 20개)
     */
    @Query("SELECT s FROM StockMaster s WHERE s.stockCode LIKE %:stockCode% AND s.isActive = true ORDER BY s.stockCode")
    List<StockMaster> findByStockCodeContainingAndIsActiveTrue(@Param("stockCode") String stockCode);

    /**
     * 통합 검색 (회사명, 영문명, 종목코드 모두 검색)
     *
     * @param keyword 검색 키워드
     * @return 일치하는 종목 목록 (최대 20개, 관련도 순으로 정렬)
     */
    @Query("""
        SELECT s FROM StockMaster s
        WHERE s.isActive = true
        AND (
            s.companyName LIKE %:keyword%
            OR s.companyNameEn LIKE %:keyword%
            OR s.stockCode LIKE %:keyword%
        )
        ORDER BY
            CASE
                WHEN s.stockCode = :keyword THEN 1
                WHEN s.companyName = :keyword THEN 2
                WHEN s.stockCode LIKE :keyword% THEN 3
                WHEN s.companyName LIKE :keyword% THEN 4
                ELSE 5
            END,
            s.companyName
        """)
    List<StockMaster> findByKeywordWithRelevanceRanking(@Param("keyword") String keyword);

    /**
     * 시장구분별 종목 조회
     *
     * @param marketType 시장구분 (KOSPI/KOSDAQ)
     * @return 해당 시장의 활성 종목 목록
     */
    @Query("SELECT s FROM StockMaster s WHERE s.marketType = :marketType AND s.isActive = true ORDER BY s.companyName")
    List<StockMaster> findByMarketTypeAndIsActiveTrue(@Param("marketType") String marketType);

    /**
     * 업종별 종목 조회
     *
     * @param sector 업종명
     * @return 해당 업종의 활성 종목 목록
     */
    @Query("SELECT s FROM StockMaster s WHERE s.sector = :sector AND s.isActive = true ORDER BY s.companyName")
    List<StockMaster> findBySectorAndIsActiveTrue(@Param("sector") String sector);

    /**
     * 활성 종목 전체 조회 (페이징 없음)
     *
     * @return 모든 활성 종목 목록 (회사명 순)
     */
    @Query("SELECT s FROM StockMaster s WHERE s.isActive = true ORDER BY s.companyName")
    List<StockMaster> findAllActiveStocks();

    /**
     * 인기 종목 조회 (주요 대형주 위주)
     *
     * @return 주요 대형주 종목 목록 (시가총액 상위)
     */
    @Query("""
        SELECT s FROM StockMaster s
        WHERE s.isActive = true
        AND s.stockCode IN ('005930', '000660', '373220', '207940', '051910', '006400', '035420', '005490', '068270', '105560')
        ORDER BY s.stockCode
        """)
    List<StockMaster> findPopularStocks();

    /**
     * 종목코드 존재 여부 확인
     *
     * @param stockCode 확인할 종목코드
     * @return 존재 여부
     */
    boolean existsByStockCodeAndIsActiveTrue(String stockCode);

    /**
     * 회사명 중복 확인
     *
     * @param companyName 확인할 회사명
     * @return 존재 여부
     */
    boolean existsByCompanyNameAndIsActiveTrue(String companyName);
}