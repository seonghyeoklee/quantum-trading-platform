package com.quantum.core.domain.model.kis;

import com.quantum.core.infrastructure.common.BaseTimeEntity;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.Comment;

import java.time.LocalDateTime;

/**
 * KIS API 원본 데이터 JSON 저장소 - 무제한 확장성 지원
 */
@Entity
@Table(name = "tb_kis_raw_data_store", 
       indexes = {
           @Index(name = "idx_kis_raw_symbol_time", columnList = "symbol, query_time"),
           @Index(name = "idx_kis_raw_api_type", columnList = "api_type"),
           @Index(name = "idx_kis_raw_symbol_api", columnList = "symbol, api_type")
       })
@Getter
@Builder
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor(access = AccessLevel.PRIVATE)
@Comment("KIS API 원본 응답 JSON 저장소")
public class KisRawDataStore extends BaseTimeEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "symbol", length = 20, nullable = false)
    @Comment("종목코드")
    private String symbol;

    @Column(name = "api_type", length = 50, nullable = false)
    @Comment("API 타입 (CURRENT_PRICE, CANDLE, ORDER 등)")
    private String apiType;

    @Column(name = "json_data", columnDefinition = "TEXT")
    @Comment("KIS API 원본 응답 JSON 데이터")
    private String jsonData;

    @Column(name = "query_time", nullable = false)
    @Comment("조회 시간")
    private LocalDateTime queryTime;

    /**
     * 팩토리 메서드 - JSON 원본 저장용
     */
    public static KisRawDataStore createCurrentPriceStore(String symbol, String jsonData) {
        return KisRawDataStore.builder()
                .symbol(symbol)
                .apiType("CURRENT_PRICE")
                .jsonData(jsonData)
                .queryTime(LocalDateTime.now())
                .build();
    }

    /**
     * 팩토리 메서드 - 다양한 API 타입 지원
     */
    public static KisRawDataStore createStore(String symbol, String apiType, String jsonData) {
        return KisRawDataStore.builder()
                .symbol(symbol)
                .apiType(apiType)
                .jsonData(jsonData)
                .queryTime(LocalDateTime.now())
                .build();
    }
}