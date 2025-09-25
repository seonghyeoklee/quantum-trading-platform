package com.quantum.backtest.infrastructure.persistence;

import com.quantum.backtest.domain.Trade;
import com.quantum.backtest.domain.TradeType;
import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 거래 내역 JPA 엔티티
 */
@Entity
@Table(name = "trades")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TradeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "backtest_id", nullable = false)
    private BacktestEntity backtest;

    @Column(name = "trade_timestamp", nullable = false)
    private LocalDateTime timestamp;

    @Enumerated(EnumType.STRING)
    @Column(name = "trade_type", nullable = false)
    private TradeType type;

    @Column(name = "price", nullable = false, precision = 10, scale = 2)
    private BigDecimal price;

    @Column(name = "quantity", nullable = false)
    private Integer quantity;

    @Column(name = "amount", nullable = false, precision = 15, scale = 2)
    private BigDecimal amount;

    @Column(name = "reason", length = 500)
    private String reason;

    /**
     * 도메인 객체로부터 엔티티를 생성한다.
     */
    public static TradeEntity from(Trade trade, BacktestEntity backtest) {
        TradeEntity entity = new TradeEntity();
        entity.backtest = backtest;
        entity.timestamp = trade.timestamp();
        entity.type = trade.type();
        entity.price = trade.price();
        entity.quantity = trade.quantity();
        entity.amount = trade.amount();
        entity.reason = trade.reason();
        return entity;
    }

    /**
     * 엔티티를 도메인 객체로 변환한다.
     */
    public Trade toDomain() {
        return new Trade(
                timestamp,
                type,
                price,
                quantity,
                amount,
                reason
        );
    }
}