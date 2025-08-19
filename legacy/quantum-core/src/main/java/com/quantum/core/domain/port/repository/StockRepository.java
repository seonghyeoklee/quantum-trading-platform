package com.quantum.core.domain.port.repository;

import com.quantum.core.domain.model.stock.Stock;
import java.util.List;
import java.util.Optional;

/**
 * 주식 정보 리포지토리 포트
 *
 * <p>주식 정보의 영속성 계층에 대한 추상화 인터페이스입니다. 도메인 계층에서 인프라스트럭처 계층의 구현체에 의존하지 않도록 하는 의존성 역전 원칙(DIP)을 적용한
 * 포트입니다.
 */
public interface StockRepository {

    /**
     * 종목코드로 주식 정보를 조회합니다.
     *
     * @param symbol 조회할 종목코드 (예: "005930")
     * @return 조회된 주식 정보, 존재하지 않으면 Optional.empty()
     */
    Optional<Stock> findBySymbol(String symbol);

    /**
     * 모든 주식 정보를 조회합니다.
     *
     * @return 전체 주식 정보 목록
     */
    List<Stock> findAll();

    /**
     * 특정 거래소의 주식 정보를 조회합니다.
     *
     * @param exchange 거래소 구분 (예: "KOSPI", "KOSDAQ")
     * @return 해당 거래소의 주식 정보 목록
     */
    List<Stock> findByExchange(String exchange);

    /**
     * 주식 정보를 저장하거나 업데이트합니다.
     *
     * @param stock 저장할 주식 정보
     * @return 저장된 주식 정보
     * @throws IllegalArgumentException stock이 null인 경우
     */
    Stock save(Stock stock);

    /**
     * 주식 정보를 삭제합니다.
     *
     * @param stock 삭제할 주식 정보
     * @throws IllegalArgumentException stock이 null인 경우
     */
    void delete(Stock stock);

    /**
     * 종목코드로 주식 정보의 존재 여부를 확인합니다.
     *
     * @param symbol 확인할 종목코드
     * @return 존재하면 true, 그렇지 않으면 false
     */
    boolean existsBySymbol(String symbol);
}
