package com.quantum.external.infrastructure.adapter.out.dart;

import com.quantum.external.application.port.out.DisclosureApiPort;
import com.quantum.external.domain.disclosure.Disclosure;
import com.quantum.external.domain.disclosure.DisclosureType;
import com.quantum.external.infrastructure.adapter.out.dart.dto.DartDisclosureResponse;
import com.quantum.external.infrastructure.config.DartProperties;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;

/**
 * DART(금융감독원 전자공시) API 어댑터
 *
 * API 스펙:
 * - 엔드포인트: https://opendart.fss.or.kr/api/list.json
 * - 인증: API Key (쿼리 파라미터 crtfc_key)
 * - 요청 파라미터: bgn_de, end_de, stock_code, page_no, page_count
 * - Rate Limit: 일 10,000건
 */
@Component
public class DartAdapter implements DisclosureApiPort {

    private static final Logger log = LoggerFactory.getLogger(DartAdapter.class);
    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyyMMdd");
    private static final int DEFAULT_PAGE_COUNT = 100;  // 최대 100개

    private final RestClient dartRestClient;
    private final DartProperties dartProperties;

    public DartAdapter(@Qualifier("dartRestClient") RestClient dartRestClient,
                      DartProperties dartProperties) {
        this.dartRestClient = dartRestClient;
        this.dartProperties = dartProperties;
    }

    @Override
    public List<Disclosure> searchDisclosures(String stockCode, LocalDate startDate, LocalDate endDate) {
        log.info("DART 공시 검색 시작: stockCode={}, startDate={}, endDate={}", stockCode, startDate, endDate);

        try {
            // DART API 호출
            DartDisclosureResponse response = dartRestClient.get()
                    .uri(uriBuilder -> uriBuilder
                            .path("/api/list.json")
                            .queryParam("crtfc_key", dartProperties.apiKey())
                            .queryParam("corp_code", stockCode)
                            .queryParam("bgn_de", startDate.format(DATE_FORMATTER))
                            .queryParam("end_de", endDate.format(DATE_FORMATTER))
                            .queryParam("page_count", DEFAULT_PAGE_COUNT)
                            .build())
                    .retrieve()
                    .body(DartDisclosureResponse.class);

            if (response == null || !response.isSuccess()) {
                log.warn("DART API 응답 실패: status={}, message={}",
                        response != null ? response.status() : "null",
                        response != null ? response.message() : "null response");
                return List.of();
            }

            if (response.list() == null || response.list().isEmpty()) {
                log.info("DART 공시 검색 결과 없음: stockCode={}", stockCode);
                return List.of();
            }

            // Disclosure 도메인 객체로 변환
            List<Disclosure> disclosures = new ArrayList<>();
            for (DartDisclosureResponse.DisclosureItem item : response.list()) {
                try {
                    Disclosure disclosure = convertToDisclosure(item);
                    disclosures.add(disclosure);
                } catch (Exception e) {
                    log.warn("공시 항목 변환 실패: reportName={}, error={}", item.reportName(), e.getMessage());
                }
            }

            log.info("DART 공시 검색 완료: stockCode={}, total={}, converted={}",
                    stockCode, response.totalCount(), disclosures.size());

            return disclosures;

        } catch (Exception e) {
            log.error("DART API 호출 실패: stockCode={}, error={}", stockCode, e.getMessage(), e);
            return List.of();
        }
    }

    /**
     * DartDisclosureResponse.DisclosureItem을 Disclosure 도메인 객체로 변환
     */
    private Disclosure convertToDisclosure(DartDisclosureResponse.DisclosureItem item) {
        // 접수일자를 LocalDateTime으로 변환 (YYYYMMDD → YYYY-MM-DD 00:00:00)
        LocalDateTime filedDate = LocalDate.parse(item.receiptDate(), DATE_FORMATTER).atStartOfDay();

        // 공시 유형 분류
        DisclosureType type = classifyDisclosureType(item.reportName());

        return new Disclosure(
                item.reportName(),
                item.corpName(),
                filedDate,
                type,
                buildDisclosureUrl(item.receiptNo()),
                item.remark()
        );
    }

    /**
     * 공시 상세 URL 생성
     */
    private String buildDisclosureUrl(String receiptNo) {
        return "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=" + receiptNo;
    }

    /**
     * 보고서명으로 공시 유형 분류
     */
    private DisclosureType classifyDisclosureType(String reportName) {
        if (reportName == null || reportName.isEmpty()) {
            return DisclosureType.OTHER;
        }

        // 정기공시
        if (reportName.contains("사업보고서") || reportName.contains("분기보고서") ||
            reportName.contains("반기보고서")) {
            return DisclosureType.REGULAR;
        }

        // 주요사항보고
        if (reportName.contains("주요사항보고") || reportName.contains("풍문또는보도") ||
            reportName.contains("조회공시") || reportName.contains("기타주요경영사항")) {
            return DisclosureType.MAJOR_ISSUE;
        }

        // 발행공시
        if (reportName.contains("증권발행") || reportName.contains("유상증자") ||
            reportName.contains("무상증자") || reportName.contains("전환사채")) {
            return DisclosureType.ISSUANCE;
        }

        // 지분공시
        if (reportName.contains("지분공시") || reportName.contains("임원ㆍ주요주주특정증권") ||
            reportName.contains("자기주식")) {
            return DisclosureType.OWNERSHIP;
        }

        // 기타
        return DisclosureType.OTHER;
    }
}
