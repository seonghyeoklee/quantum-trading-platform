package com.quantum.external.infrastructure.adapter.out.dart;

import com.quantum.external.domain.disclosure.Disclosure;
import com.quantum.external.infrastructure.config.DartProperties;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.web.client.RestClient;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * DartAdapter 통합 테스트
 * 실제 DART API 호출
 */
@SpringBootTest
@ActiveProfiles("test")
class DartAdapterTest {

    @Autowired
    @Qualifier("dartRestClient")
    private RestClient dartRestClient;

    @Autowired
    private DartProperties dartProperties;

    @Test
    void 삼성전자_공시_검색() {
        // Given
        DartAdapter dartAdapter = new DartAdapter(dartRestClient, dartProperties);
        String stockCode = "005930";  // 삼성전자 종목코드
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(30);  // 최근 30일

        // When
        List<Disclosure> disclosures = dartAdapter.searchDisclosures(stockCode, startDate, endDate);

        // Then
        assertNotNull(disclosures, "공시 목록이 null이면 안됩니다");

        System.out.println("=== 삼성전자 공시 검색 결과 ===");
        System.out.println("검색 기간: " + startDate + " ~ " + endDate);
        System.out.println("총 검색 결과: " + disclosures.size() + "건");
        System.out.println();

        if (!disclosures.isEmpty()) {
            Disclosure firstDisclosure = disclosures.get(0);
            assertNotNull(firstDisclosure.title(), "제목이 null이면 안됩니다");
            assertNotNull(firstDisclosure.companyName(), "회사명이 null이면 안됩니다");
            assertNotNull(firstDisclosure.filedDate(), "접수일이 null이면 안됩니다");
            assertNotNull(firstDisclosure.type(), "공시유형이 null이면 안됩니다");
            assertNotNull(firstDisclosure.url(), "URL이 null이면 안됩니다");

            System.out.println("첫 번째 공시:");
            System.out.println("제목: " + firstDisclosure.title());
            System.out.println("회사명: " + firstDisclosure.companyName());
            System.out.println("접수일: " + firstDisclosure.filedDate());
            System.out.println("공시유형: " + firstDisclosure.type());
            System.out.println("URL: " + firstDisclosure.url());

            if (firstDisclosure.summary() != null && !firstDisclosure.summary().isEmpty()) {
                System.out.println("비고: " + firstDisclosure.summary());
            }
        }
    }

    @Test
    void 빈_결과_처리() {
        // Given
        DartAdapter dartAdapter = new DartAdapter(dartRestClient, dartProperties);
        String stockCode = "999999";  // 존재하지 않는 종목코드
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(1);

        // When
        List<Disclosure> disclosures = dartAdapter.searchDisclosures(stockCode, startDate, endDate);

        // Then
        assertNotNull(disclosures, "공시 목록이 null이면 안됩니다");

        System.out.println("=== 존재하지 않는 종목코드 공시 검색 결과 ===");
        System.out.println("총 검색 결과: " + disclosures.size() + "건");
    }
}
