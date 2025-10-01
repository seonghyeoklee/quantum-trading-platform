package com.quantum.external.infrastructure.adapter.out.naver;

import com.quantum.external.domain.news.News;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.time.LocalDate;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * NaverNewsAdapter 통합 테스트
 * 실제 네이버 뉴스 API 호출
 */
@SpringBootTest
@ActiveProfiles("test")
class NaverNewsAdapterTest {

    @Autowired
    private NaverNewsAdapter naverNewsAdapter;

    @Test
    void 삼성전자_뉴스_검색() {
        // Given
        String keyword = "삼성전자";
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(7);  // 최근 7일

        // When
        List<News> newsList = naverNewsAdapter.searchNews(keyword, startDate, endDate);

        // Then
        assertNotNull(newsList, "뉴스 목록이 null이면 안됩니다");
        assertFalse(newsList.isEmpty(), "뉴스가 최소 1개 이상 있어야 합니다");

        // 첫 번째 뉴스 검증
        News firstNews = newsList.get(0);
        assertNotNull(firstNews.title(), "제목이 null이면 안됩니다");
        assertNotNull(firstNews.content(), "내용이 null이면 안됩니다");
        assertNotNull(firstNews.publishedDate(), "발행일이 null이면 안됩니다");
        assertNotNull(firstNews.url(), "URL이 null이면 안됩니다");
        assertNotNull(firstNews.source(), "출처가 null이면 안됩니다");

        // HTML 태그 제거 확인
        assertFalse(firstNews.title().contains("<b>"), "제목에 <b> 태그가 있으면 안됩니다");
        assertFalse(firstNews.title().contains("</b>"), "제목에 </b> 태그가 있으면 안됩니다");

        // 날짜 범위 확인
        LocalDate publishedDate = firstNews.publishedDate().toLocalDate();
        assertTrue(!publishedDate.isBefore(startDate) && !publishedDate.isAfter(endDate),
                "발행일이 검색 범위를 벗어났습니다");

        // 결과 출력
        System.out.println("=== 삼성전자 뉴스 검색 결과 ===");
        System.out.println("검색 기간: " + startDate + " ~ " + endDate);
        System.out.println("총 검색 결과: " + newsList.size() + "건");
        System.out.println();
        System.out.println("첫 번째 뉴스:");
        System.out.println("제목: " + firstNews.title());
        System.out.println("내용: " + firstNews.content());
        System.out.println("발행일: " + firstNews.publishedDate());
        System.out.println("출처: " + firstNews.source());
        System.out.println("URL: " + firstNews.url());
    }

    @Test
    void 종목코드로_뉴스_검색() {
        // Given
        String keyword = "005930";  // 삼성전자 종목코드
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(3);

        // When
        List<News> newsList = naverNewsAdapter.searchNews(keyword, startDate, endDate);

        // Then
        assertNotNull(newsList, "뉴스 목록이 null이면 안됩니다");

        System.out.println("=== 종목코드(005930) 뉴스 검색 결과 ===");
        System.out.println("총 검색 결과: " + newsList.size() + "건");
    }

    @Test
    void 빈_결과_처리() {
        // Given
        String keyword = "asdfqwerzxcv1234567890";  // 존재하지 않는 키워드
        LocalDate endDate = LocalDate.now();
        LocalDate startDate = endDate.minusDays(1);

        // When
        List<News> newsList = naverNewsAdapter.searchNews(keyword, startDate, endDate);

        // Then
        assertNotNull(newsList, "뉴스 목록이 null이면 안됩니다");
        assertTrue(newsList.isEmpty(), "존재하지 않는 키워드는 빈 리스트를 반환해야 합니다");
    }
}
