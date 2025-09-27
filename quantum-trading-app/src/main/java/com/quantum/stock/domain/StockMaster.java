package com.quantum.stock.domain;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.ToString;

import java.time.LocalDateTime;

/**
 * 종목 마스터 정보 JPA 엔티티
 *
 * DINO 통합 분석 시스템의 종목 검색 기능을 위한 엔티티
 * 종목코드, 회사명, 시장구분, 업종 등 기본 정보를 저장
 */
@Entity
@Table(name = "stock_master", indexes = {
    @Index(name = "idx_stock_master_company_name", columnList = "company_name"),
    @Index(name = "idx_stock_master_market_type", columnList = "market_type"),
    @Index(name = "idx_stock_master_sector", columnList = "sector"),
    @Index(name = "idx_stock_master_active", columnList = "is_active")
})
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@ToString
public class StockMaster {

    /**
     * 6자리 종목코드 (예: 005930)
     */
    @Id
    @Column(name = "stock_code", length = 6)
    private String stockCode;

    /**
     * 회사명 (예: 삼성전자)
     */
    @Column(name = "company_name", nullable = false, length = 100)
    private String companyName;

    /**
     * 영문 회사명 (예: Samsung Electronics Co., Ltd.)
     */
    @Column(name = "company_name_en", length = 100)
    private String companyNameEn;

    /**
     * 시장구분 (KOSPI/KOSDAQ)
     */
    @Column(name = "market_type", length = 10)
    private String marketType;

    /**
     * 업종 (예: 전기전자, 화학, 의약품 등)
     */
    @Column(name = "sector", length = 50)
    private String sector;

    /**
     * 상장여부 (true: 상장, false: 폐지)
     */
    @Column(name = "is_active", columnDefinition = "BOOLEAN DEFAULT TRUE")
    private Boolean isActive = true;

    /**
     * 생성일시
     */
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    /**
     * 수정일시
     */
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    /**
     * 생성자
     *
     * @param stockCode 종목코드 (6자리)
     * @param companyName 회사명
     * @param companyNameEn 영문 회사명
     * @param marketType 시장구분
     * @param sector 업종
     */
    public StockMaster(String stockCode, String companyName, String companyNameEn,
                       String marketType, String sector) {
        this.stockCode = stockCode;
        this.companyName = companyName;
        this.companyNameEn = companyNameEn;
        this.marketType = marketType;
        this.sector = sector;
        this.isActive = true;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 종목 정보 업데이트
     *
     * @param companyName 회사명
     * @param companyNameEn 영문 회사명
     * @param marketType 시장구분
     * @param sector 업종
     */
    public void updateStockInfo(String companyName, String companyNameEn,
                               String marketType, String sector) {
        this.companyName = companyName;
        this.companyNameEn = companyNameEn;
        this.marketType = marketType;
        this.sector = sector;
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 상장 상태 변경
     *
     * @param isActive 상장여부
     */
    public void updateActiveStatus(Boolean isActive) {
        this.isActive = isActive;
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * JPA 생성 전 처리
     */
    @PrePersist
    protected void onCreate() {
        if (this.createdAt == null) {
            this.createdAt = LocalDateTime.now();
        }
        if (this.updatedAt == null) {
            this.updatedAt = LocalDateTime.now();
        }
        if (this.isActive == null) {
            this.isActive = true;
        }
    }

    /**
     * JPA 업데이트 전 처리
     */
    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 검색용 표시명 반환 (종목코드 + 회사명)
     *
     * @return 표시명 (예: "005930 삼성전자")
     */
    public String getDisplayName() {
        return String.format("%s %s", this.stockCode, this.companyName);
    }

    /**
     * 검색용 전체 정보 반환 (종목코드 + 회사명 + 영문명)
     *
     * @return 전체 정보 (예: "005930 삼성전자 Samsung Electronics")
     */
    public String getFullDisplayName() {
        if (this.companyNameEn != null && !this.companyNameEn.trim().isEmpty()) {
            return String.format("%s %s %s", this.stockCode, this.companyName, this.companyNameEn);
        }
        return getDisplayName();
    }

    /**
     * 종목이 활성 상태인지 확인
     *
     * @return true if 상장 중, false if 폐지
     */
    public boolean isActiveStock() {
        return this.isActive != null && this.isActive;
    }
}