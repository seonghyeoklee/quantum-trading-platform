package com.quantum.external.application.port.out;

import com.quantum.external.domain.disclosure.Disclosure;

import java.time.LocalDate;
import java.util.List;

/**
 * 공시 API 포트 (외부 시스템 추상화)
 * 구현체: DartAdapter 등
 */
public interface DisclosureApiPort {

    /**
     * 종목 공시 검색
     *
     * @param stockCode 종목코드
     * @param startDate 시작일
     * @param endDate 종료일
     * @return 공시 목록
     */
    List<Disclosure> searchDisclosures(String stockCode, LocalDate startDate, LocalDate endDate);
}
