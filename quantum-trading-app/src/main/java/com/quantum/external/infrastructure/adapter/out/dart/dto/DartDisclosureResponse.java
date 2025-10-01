package com.quantum.external.infrastructure.adapter.out.dart.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * DART 공시검색 API 응답
 */
public record DartDisclosureResponse(
        @JsonProperty("status")
        String status,              // 에러 및 정보 코드 (000: 정상)

        @JsonProperty("message")
        String message,             // 에러 및 정보 메시지

        @JsonProperty("page_no")
        int pageNo,                 // 페이지 번호

        @JsonProperty("page_count")
        int pageCount,              // 페이지당 건수

        @JsonProperty("total_count")
        int totalCount,             // 총 건수

        @JsonProperty("total_page")
        int totalPage,              // 총 페이지 수

        @JsonProperty("list")
        List<DisclosureItem> list   // 공시 목록
) {
    /**
     * 공시 항목
     */
    public record DisclosureItem(
            @JsonProperty("corp_code")
            String corpCode,            // 고유번호 (8자리)

            @JsonProperty("corp_name")
            String corpName,            // 회사명

            @JsonProperty("stock_code")
            String stockCode,           // 종목코드 (6자리, 상장사만)

            @JsonProperty("corp_cls")
            String corpCls,             // 법인구분 (Y: 유가, K: 코스닥, N: 코넥스, E: 기타)

            @JsonProperty("report_nm")
            String reportName,          // 보고서명

            @JsonProperty("rcept_no")
            String receiptNo,           // 접수번호 (14자리)

            @JsonProperty("flr_nm")
            String filerName,           // 공시 제출인명

            @JsonProperty("rcept_dt")
            String receiptDate,         // 접수일자 (YYYYMMDD)

            @JsonProperty("rm")
            String remark               // 비고
    ) {
    }

    /**
     * API 호출 성공 여부
     */
    public boolean isSuccess() {
        return "000".equals(status);
    }
}
