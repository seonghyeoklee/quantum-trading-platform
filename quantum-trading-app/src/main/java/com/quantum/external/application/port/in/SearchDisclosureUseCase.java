package com.quantum.external.application.port.in;

import com.quantum.external.domain.disclosure.Disclosure;
import com.quantum.external.domain.disclosure.DisclosureAnalysisResult;

import java.time.LocalDate;
import java.util.List;

/**
 * 공시 검색 Use Case
 */
public interface SearchDisclosureUseCase {

    /**
     * 종목 공시 검색
     */
    List<Disclosure> searchDisclosures(String stockCode, LocalDate startDate, LocalDate endDate);

    /**
     * 종목 공시 분석
     */
    DisclosureAnalysisResult analyzeStockDisclosures(String stockCode, int recentDays);
}
