package com.quantum.external.application.service;

import com.quantum.external.application.port.in.SearchDisclosureUseCase;
import com.quantum.external.application.port.out.DisclosureApiPort;
import com.quantum.external.domain.disclosure.Disclosure;
import com.quantum.external.domain.disclosure.DisclosureAnalysisResult;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.List;

/**
 * 공시 서비스
 * TODO: 비즈니스 로직 구현
 */
@Service
public class DisclosureService implements SearchDisclosureUseCase {

    private final DisclosureApiPort disclosureApiPort;

    public DisclosureService(DisclosureApiPort disclosureApiPort) {
        this.disclosureApiPort = disclosureApiPort;
    }

    @Override
    public List<Disclosure> searchDisclosures(String stockCode, LocalDate startDate, LocalDate endDate) {
        // TODO: 공시 검색 로직 구현
        return disclosureApiPort.searchDisclosures(stockCode, startDate, endDate);
    }

    @Override
    public DisclosureAnalysisResult analyzeStockDisclosures(String stockCode, int recentDays) {
        // TODO: 공시 분석 로직 구현
        // 1. 최근 N일 공시 수집
        // 2. 공시 유형별 재료성 판단
        // 3. 재료 점수 계산
        throw new UnsupportedOperationException("공시 분석 로직 구현 필요");
    }
}
