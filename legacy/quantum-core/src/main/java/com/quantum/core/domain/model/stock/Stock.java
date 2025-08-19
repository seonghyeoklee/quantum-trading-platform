package com.quantum.core.domain.model.stock;

import com.quantum.core.domain.model.common.ExchangeCode;
import com.quantum.core.infrastructure.common.BaseTimeEntity;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Objects;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

/** 주식 정보 도메인 엔티티 */
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(name = "tb_stock")
public class Stock extends BaseTimeEntity {

    @Id
    @Column(name = "symbol")
    @Comment("종목코드")
    private String symbol;

    @Column(name = "name", nullable = false)
    @Comment("종목명")
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(name = "exchange", nullable = false)
    @Comment("거래소")
    private ExchangeCode exchange;

    @Column(name = "last_updated")
    @Comment("최종업데이트시간")
    private LocalDateTime lastUpdated;

    @Column(name = "current_price", precision = 19, scale = 2)
    @Comment("현재가")
    private BigDecimal currentPrice;

    @Column(name = "previous_close_price", precision = 19, scale = 2)
    @Comment("전일종가")
    private BigDecimal previousClosePrice;

    @Column(name = "price_change", precision = 19, scale = 2)
    @Comment("전일대비금액")
    private BigDecimal priceChange;

    @Column(name = "change_rate", precision = 5, scale = 2)
    @Comment("전일대비등락률")
    private BigDecimal changeRate;

    @Column(name = "volume")
    @Comment("거래량")
    private Long volume;

    @Column(name = "high_price", precision = 19, scale = 2)
    @Comment("고가")
    private BigDecimal high;

    @Column(name = "low_price", precision = 19, scale = 2)
    @Comment("저가")
    private BigDecimal low;

    @Builder
    public Stock(
            String symbol,
            String name,
            ExchangeCode exchange,
            BigDecimal currentPrice,
            BigDecimal previousClosePrice,
            BigDecimal priceChange,
            BigDecimal changeRate,
            Long volume,
            BigDecimal high,
            BigDecimal low,
            LocalDateTime lastUpdated) {
        if (symbol == null || symbol.trim().isEmpty()) {
            throw new IllegalArgumentException("종목코드는 필수입니다");
        }
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("종목명은 필수입니다");
        }
        if (exchange == null) {
            throw new IllegalArgumentException("거래소는 필수입니다");
        }

        this.symbol = symbol.trim();
        this.name = name.trim();
        this.exchange = exchange;
        this.currentPrice = currentPrice;
        this.previousClosePrice = previousClosePrice;
        this.priceChange = priceChange;
        this.changeRate = changeRate;
        this.volume = volume;
        this.high = high;
        this.low = low;
        this.lastUpdated = lastUpdated != null ? lastUpdated : LocalDateTime.now();
    }

    /** 기본 정보로 Stock 생성 (팩토리 메서드) */
    public static Stock of(String symbol, String name, BigDecimal currentPrice) {
        return Stock.builder()
            .symbol(symbol)
            .name(name)
            .exchange(ExchangeCode.KOSPI)  // 기본값
            .currentPrice(currentPrice)
            .build();
    }

    /** 주식 가격 정보 업데이트 (Spring Batch용) */
    public void updatePrice(
            BigDecimal currentPrice, BigDecimal priceChange, BigDecimal changeRate) {
        if (currentPrice != null && currentPrice.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("현재가는 0보다 큰 값이어야 합니다");
        }

        this.currentPrice = currentPrice;
        this.priceChange = priceChange;
        this.changeRate = changeRate;
        this.lastUpdated = LocalDateTime.now();
    }

    /** 주식 가격 정보 업데이트 (전일종가 포함) */
    public void updatePrice(
            BigDecimal currentPrice,
            BigDecimal previousClosePrice,
            BigDecimal priceChange,
            BigDecimal changeRate) {
        if (currentPrice != null && currentPrice.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("현재가는 0보다 큰 값이어야 합니다");
        }

        this.currentPrice = currentPrice;
        this.previousClosePrice = previousClosePrice;
        this.priceChange = priceChange;
        this.changeRate = changeRate;
        this.lastUpdated = LocalDateTime.now();
    }

    /** 거래 정보 업데이트 (Spring Batch용) */
    public void updateTradingInfo(Long volume, LocalDateTime lastUpdated) {
        if (volume != null && volume < 0) {
            throw new IllegalArgumentException("거래량은 0 이상이어야 합니다");
        }

        this.volume = volume;
        this.lastUpdated = lastUpdated != null ? lastUpdated : LocalDateTime.now();
    }

    /** 종목명 업데이트 */
    public void updateName(String name) {
        if (name == null || name.trim().isEmpty()) {
            throw new IllegalArgumentException("종목명은 필수입니다");
        }
        this.name = name.trim();
    }

    /** 거래량 및 고저가 정보 업데이트 */
    public void updateTradingInfo(Long volume, BigDecimal high, BigDecimal low) {
        if (volume != null && volume < 0) {
            throw new IllegalArgumentException("거래량은 0 이상이어야 합니다");
        }
        if (high != null && high.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("고가는 0보다 큰 값이어야 합니다");
        }
        if (low != null && low.compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("저가는 0보다 큰 값이어야 합니다");
        }

        this.volume = volume;
        this.high = high;
        this.low = low;
    }

    /** 상승인지 확인 */
    public boolean isPositiveChange() {
        return priceChange != null && priceChange.compareTo(BigDecimal.ZERO) > 0;
    }

    /** 하락인지 확인 */
    public boolean isNegativeChange() {
        return priceChange != null && priceChange.compareTo(BigDecimal.ZERO) < 0;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Stock stock = (Stock) o;
        return Objects.equals(symbol, stock.symbol);
    }

    @Override
    public int hashCode() {
        return Objects.hash(symbol);
    }

    @Override
    public String toString() {
        return String.format(
                "Stock{symbol='%s', name='%s', currentPrice=%s, changeRate=%s%%}",
                symbol, name, currentPrice, changeRate);
    }
}
