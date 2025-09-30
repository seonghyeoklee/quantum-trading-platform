package com.quantum.dino.infrastructure.persistence;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantum.dino.dto.CalculationStep;
import com.quantum.dino.dto.DinoFinanceResult;
import jakarta.persistence.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * DINO 재무 분석 결과 JPA 엔티티
 *
 * H2 데이터베이스에 분석 결과를 저장하기 위한 엔티티
 */
@Entity
@Table(name = "dino_finance_results",
       uniqueConstraints = @UniqueConstraint(columnNames = {"stock_code", "analysis_date"}))
@EntityListeners(AuditingEntityListener.class)
public class DinoFinanceResultEntity {

    private static final Logger log = LoggerFactory.getLogger(DinoFinanceResultEntity.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "stock_code", nullable = false, length = 10)
    private String stockCode;

    @Column(name = "company_name", length = 100)
    private String companyName;

    // 개별 지표 점수
    @Column(name = "revenue_growth_score")
    private Integer revenueGrowthScore;

    @Column(name = "operating_profit_score")
    private Integer operatingProfitScore;

    @Column(name = "operating_margin_score")
    private Integer operatingMarginScore;

    @Column(name = "retention_rate_score")
    private Integer retentionRateScore;

    @Column(name = "debt_ratio_score")
    private Integer debtRatioScore;

    @Column(name = "total_score")
    private Integer totalScore;

    @Column(name = "grade", length = 5)
    private String grade;

    // 상세 계산 결과 (H2에서 precision/scale 사용 안함)
    @Column(name = "revenue_growth_rate")
    private Double revenueGrowthRate;

    @Column(name = "operating_profit_transition", length = 20)
    private String operatingProfitTransition;

    @Column(name = "operating_margin_rate")
    private Double operatingMarginRate;

    @Column(name = "retention_rate")
    private Double retentionRate;

    @Column(name = "debt_ratio")
    private Double debtRatio;

    // 원본 데이터 (검증용) - H2에서는 precision/scale 없이 사용
    @Column(name = "current_revenue")
    private BigDecimal currentRevenue;

    @Column(name = "previous_revenue")
    private BigDecimal previousRevenue;

    @Column(name = "current_operating_profit")
    private BigDecimal currentOperatingProfit;

    @Column(name = "previous_operating_profit")
    private BigDecimal previousOperatingProfit;

    @Column(name = "total_debt")
    private BigDecimal totalDebt;

    @Column(name = "total_equity")
    private BigDecimal totalEquity;

    @Column(name = "retained_earnings")
    private BigDecimal retainedEarnings;

    @Column(name = "capital_stock")
    private BigDecimal capitalStock;

    // 데이터 기준 연월
    @Column(name = "current_period", length = 20)
    private String currentPeriod;

    @Column(name = "previous_period", length = 20)
    private String previousPeriod;

    // 분석 날짜 (하루 1회 제한용)
    @Column(name = "analysis_date", nullable = false)
    private LocalDateTime analysisDate;

    // 계산 과정 저장 (JSON 형태)
    @Column(name = "calculation_steps_json", columnDefinition = "TEXT")
    private String calculationStepsJson;

    @Column(name = "final_calculation", columnDefinition = "TEXT")
    private String finalCalculation;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    // JPA 기본 생성자
    protected DinoFinanceResultEntity() {}

    // 팩토리 메서드
    public static DinoFinanceResultEntity from(DinoFinanceResult result) {
        DinoFinanceResultEntity entity = new DinoFinanceResultEntity();

        entity.stockCode = result.stockCode();
        entity.companyName = result.companyName();
        entity.revenueGrowthScore = result.revenueGrowthScore();
        entity.operatingProfitScore = result.operatingProfitScore();
        entity.operatingMarginScore = result.operatingMarginScore();
        entity.retentionRateScore = result.retentionRateScore();
        entity.debtRatioScore = result.debtRatioScore();
        entity.totalScore = result.totalScore();
        entity.grade = result.getGrade();

        entity.revenueGrowthRate = result.revenueGrowthRate();
        entity.operatingProfitTransition = result.operatingProfitTransition();
        entity.operatingMarginRate = result.operatingMarginRate();
        entity.retentionRate = result.retentionRate();
        entity.debtRatio = result.debtRatio();

        entity.currentRevenue = result.currentRevenue();
        entity.previousRevenue = result.previousRevenue();
        entity.currentOperatingProfit = result.currentOperatingProfit();
        entity.previousOperatingProfit = result.previousOperatingProfit();
        entity.totalDebt = result.totalDebt();
        entity.totalEquity = result.totalEquity();
        entity.retainedEarnings = result.retainedEarnings();
        entity.capitalStock = result.capitalStock();

        entity.currentPeriod = result.currentPeriod();
        entity.previousPeriod = result.previousPeriod();
        entity.analysisDate = result.analyzedAt();

        // 계산 과정 JSON 저장
        entity.calculationStepsJson = entity.serializeCalculationSteps(result.calculationSteps());
        entity.finalCalculation = result.finalCalculation();

        return entity;
    }

    // Getters
    public Long getId() { return id; }
    public String getStockCode() { return stockCode; }
    public String getCompanyName() { return companyName; }
    public Integer getRevenueGrowthScore() { return revenueGrowthScore; }
    public Integer getOperatingProfitScore() { return operatingProfitScore; }
    public Integer getOperatingMarginScore() { return operatingMarginScore; }
    public Integer getRetentionRateScore() { return retentionRateScore; }
    public Integer getDebtRatioScore() { return debtRatioScore; }
    public Integer getTotalScore() { return totalScore; }
    public String getGrade() { return grade; }
    public Double getRevenueGrowthRate() { return revenueGrowthRate; }
    public String getOperatingProfitTransition() { return operatingProfitTransition; }
    public Double getOperatingMarginRate() { return operatingMarginRate; }
    public Double getRetentionRate() { return retentionRate; }
    public Double getDebtRatio() { return debtRatio; }
    public BigDecimal getCurrentRevenue() { return currentRevenue; }
    public BigDecimal getPreviousRevenue() { return previousRevenue; }
    public BigDecimal getCurrentOperatingProfit() { return currentOperatingProfit; }
    public BigDecimal getPreviousOperatingProfit() { return previousOperatingProfit; }
    public BigDecimal getTotalDebt() { return totalDebt; }
    public BigDecimal getTotalEquity() { return totalEquity; }
    public BigDecimal getRetainedEarnings() { return retainedEarnings; }
    public BigDecimal getCapitalStock() { return capitalStock; }
    public String getCurrentPeriod() { return currentPeriod; }
    public String getPreviousPeriod() { return previousPeriod; }
    public LocalDateTime getAnalysisDate() { return analysisDate; }
    public String getCalculationStepsJson() { return calculationStepsJson; }
    public String getFinalCalculation() { return finalCalculation; }
    public LocalDateTime getCreatedAt() { return createdAt; }

    // 계산 과정 JSON 직렬화/역직렬화 메서드
    private String serializeCalculationSteps(List<CalculationStep> steps) {
        if (steps == null || steps.isEmpty()) {
            return null;
        }
        try {
            return objectMapper.writeValueAsString(steps);
        } catch (JsonProcessingException e) {
            log.warn("계산 과정 JSON 직렬화 실패: {}", e.getMessage());
            return null;
        }
    }

    public List<CalculationStep> deserializeCalculationSteps() {
        if (calculationStepsJson == null || calculationStepsJson.trim().isEmpty()) {
            return new ArrayList<>();
        }
        try {
            return objectMapper.readValue(calculationStepsJson, new TypeReference<List<CalculationStep>>() {});
        } catch (JsonProcessingException e) {
            log.warn("계산 과정 JSON 역직렬화 실패: {}", e.getMessage());
            return new ArrayList<>();
        }
    }
}