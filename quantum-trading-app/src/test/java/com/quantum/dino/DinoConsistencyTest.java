package com.quantum.dino;

import com.quantum.dino.dto.DinoIntegratedResult;
import com.quantum.dino.service.DinoIntegratedService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/**
 * DINO 점수 일관성 테스트
 *
 * Math.random() 제거 후 동일한 종목에 대해
 * 여러 번 분석을 실행했을 때 점수가 일관되는지 확인
 */
@SpringBootTest
@ActiveProfiles("test")
class DinoConsistencyTest {

    @Autowired
    private DinoIntegratedService dinoIntegratedService;

    @Test
    void testDinoScoreConsistency() {
        // 테스트 대상: 삼성전자 (005930)
        String stockCode = "005930";
        int testRuns = 5;

        System.out.println("=== DINO 점수 일관성 테스트 시작 ===");
        System.out.println("종목: 삼성전자 (005930)");
        System.out.println("테스트 횟수: " + testRuns + "회");
        System.out.println();

        List<Integer> totalScores = new ArrayList<>();
        List<DinoIntegratedResult> results = new ArrayList<>();

        // 5회 반복 실행
        for (int i = 1; i <= testRuns; i++) {
            try {
                System.out.print("테스트 " + i + " 실행 중... ");

                DinoIntegratedResult result = dinoIntegratedService.analyzeIntegrated(stockCode);
                results.add(result);

                if (result.isValidTotalScore()) {
                    int totalScore = result.totalScore();
                    totalScores.add(totalScore);
                    System.out.println("완료 - 총점: " + totalScore + "/20");
                } else {
                    System.out.println("실패 - 유효하지 않은 점수");
                }

                // 각 실행 간 짧은 대기
                Thread.sleep(100);

            } catch (Exception e) {
                System.out.println("실패 - 오류: " + e.getMessage());
                fail("DINO 분석 실행 중 오류 발생: " + e.getMessage());
            }
        }

        System.out.println();
        System.out.println("=== 테스트 결과 분석 ===");

        // 결과 분석
        assertFalse(totalScores.isEmpty(), "성공한 테스트 결과가 없습니다.");

        System.out.println("성공한 테스트: " + totalScores.size() + "/" + testRuns);
        System.out.println("획득한 점수들:");
        for (int i = 0; i < totalScores.size(); i++) {
            System.out.println("  " + (i + 1) + ". " + totalScores.get(i) + "/20");
        }

        // 고유 점수 개수 확인
        Set<Integer> uniqueScores = totalScores.stream().collect(Collectors.toSet());
        System.out.println("고유 점수 개수: " + uniqueScores.size());

        if (uniqueScores.size() == 1) {
            System.out.println("✅ 점수 일관성 테스트 PASS - 모든 실행에서 동일한 점수");

            // 상세 결과 비교
            DinoIntegratedResult firstResult = results.get(0);
            for (int i = 1; i < results.size(); i++) {
                DinoIntegratedResult currentResult = results.get(i);

                // 각 영역별 점수도 일치하는지 확인
                assertEquals(firstResult.financeResult().totalScore(),
                           currentResult.financeResult().totalScore(),
                           "재무분석 점수가 일치하지 않음");

                assertEquals(firstResult.technicalResult().totalScore(),
                           currentResult.technicalResult().totalScore(),
                           "기술분석 점수가 일치하지 않음");

                assertEquals(firstResult.materialResult().totalScore(),
                           currentResult.materialResult().totalScore(),
                           "재료분석 점수가 일치하지 않음");

                assertEquals(firstResult.priceResult().totalScore(),
                           currentResult.priceResult().totalScore(),
                           "가격분석 점수가 일치하지 않음");
            }

            System.out.println("✅ 각 영역별 점수도 모두 일관됨");

        } else {
            System.out.println("❌ 점수 일관성 테스트 FAIL - 실행마다 다른 점수");
            System.out.println("점수 분포:");
            uniqueScores.forEach(score -> {
                long count = totalScores.stream().filter(s -> s.equals(score)).count();
                System.out.println("  " + score + "점: " + count + "회");
            });

            fail("DINO 점수가 일관되지 않습니다. 고유 점수 개수: " + uniqueScores.size());
        }

        System.out.println();
        System.out.println("=== DINO 점수 일관성 테스트 완료 ===");
    }

    @Test
    void testIndividualScoreConsistency() {
        String stockCode = "005930";

        System.out.println("=== 개별 분석 영역 일관성 테스트 ===");

        // 첫 번째 실행
        DinoIntegratedResult result1 = dinoIntegratedService.analyzeIntegrated(stockCode);
        DinoIntegratedResult result2 = dinoIntegratedService.analyzeIntegrated(stockCode);

        // 재무분석 점수 일관성
        assertEquals(result1.financeResult().totalScore(), result2.financeResult().totalScore(),
                    "재무분석 점수 불일치");
        System.out.println("✅ 재무분석 점수 일관성 확인: " + result1.financeResult().totalScore() + "/5");

        // 기술분석 점수 일관성
        assertEquals(result1.technicalResult().totalScore(), result2.technicalResult().totalScore(),
                    "기술분석 점수 불일치");
        System.out.println("✅ 기술분석 점수 일관성 확인: " + result1.technicalResult().totalScore() + "/5");

        // 재료분석 점수 일관성
        assertEquals(result1.materialResult().totalScore(), result2.materialResult().totalScore(),
                    "재료분석 점수 불일치");
        System.out.println("✅ 재료분석 점수 일관성 확인: " + result1.materialResult().totalScore() + "/5");

        // 가격분석 점수 일관성
        assertEquals(result1.priceResult().totalScore(), result2.priceResult().totalScore(),
                    "가격분석 점수 불일치");
        System.out.println("✅ 가격분석 점수 일관성 확인: " + result1.priceResult().totalScore() + "/5");

        // 총점 일관성
        assertEquals(result1.totalScore(), result2.totalScore(),
                    "총점 불일치");
        System.out.println("✅ 총점 일관성 확인: " + result1.totalScore() + "/20");

        System.out.println("=== 개별 분석 영역 일관성 테스트 완료 ===");
    }
}