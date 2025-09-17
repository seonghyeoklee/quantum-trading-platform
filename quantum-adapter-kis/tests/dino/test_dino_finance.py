#!/usr/bin/env python3
"""
디노테스트 재무 점수 계산 테스트 스크립트

Usage:
    python test_dino_finance.py
    python test_dino_finance.py --stock-code=005930
    python test_dino_finance.py --batch
"""

import asyncio
import argparse
import logging
import sys
from decimal import Decimal

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 경로 설정
sys.path.extend(['.', 'examples_llm'])

def test_finance_scorer_unit():
    """단위 테스트: DinoTestFinanceScorer 개별 메서드 테스트"""
    logger.info("=== 디노테스트 재무 점수 계산기 단위 테스트 시작 ===")
    
    from dino_test.finance_scorer import DinoTestFinanceScorer, FinanceData
    
    scorer = DinoTestFinanceScorer()
    
    # 테스트 케이스 1: 우수한 재무상태 (예상 점수: 5점)
    excellent_data = FinanceData(
        current_revenue=Decimal('100000'),      # 100억 (매출)
        previous_revenue=Decimal('80000'),       # 80억 (전년 대비 25% 증가)
        current_operating_profit=Decimal('15000'), # 15억 (영업이익)
        previous_operating_profit=Decimal('12000'), # 12억 (흑자 지속)
        total_debt=Decimal('20000'),            # 20억 (총부채)
        total_equity=Decimal('80000'),          # 80억 (자기자본 - 부채비율 25%)
        retained_earnings=Decimal('50000'),     # 50억 (이익잉여금)
        capital_stock=Decimal('3000'),          # 30억 (자본금 - 유보율 1666%)
        operating_margin=Decimal('15')         # 15% (영업이익률)
    )
    
    result = scorer.calculate_total_finance_score(excellent_data)
    logger.info(f"우수한 재무상태 테스트 - 점수: {result.total_score}/5")
    logger.info(f"상세: 매출증감({result.revenue_growth_score}), 영업이익({result.operating_profit_score}), "
                f"영업이익률({result.operating_margin_score}), 유보율({result.retained_earnings_ratio_score}), "
                f"부채비율({result.debt_ratio_score})")
    
    # 테스트 케이스 2: 보통 재무상태 (예상 점수: 2-3점)
    average_data = FinanceData(
        current_revenue=Decimal('100000'),      # 매출 동일
        previous_revenue=Decimal('95000'),       # 5% 성장 (0점)
        current_operating_profit=Decimal('8000'),  # 영업이익 8%
        previous_operating_profit=Decimal('7000'),  # 흑자 지속 (0점)
        total_debt=Decimal('60000'),            # 부채비율 100% (0점)  
        total_equity=Decimal('60000'),          
        retained_earnings=Decimal('20000'),     # 유보율 666% (0점)
        capital_stock=Decimal('3000'),          
        operating_margin=Decimal('8')          # 영업이익률 8% (0점)
    )
    
    result = scorer.calculate_total_finance_score(average_data)
    logger.info(f"보통 재무상태 테스트 - 점수: {result.total_score}/5")
    
    # 테스트 케이스 3: 취약한 재무상태 (예상 점수: 0점)
    poor_data = FinanceData(
        current_revenue=Decimal('80000'),       # 매출 20% 감소 (-1점)
        previous_revenue=Decimal('100000'),     
        current_operating_profit=Decimal('-5000'), # 적자 전환 (-1점)
        previous_operating_profit=Decimal('2000'),  
        total_debt=Decimal('150000'),           # 부채비율 300% (-1점)
        total_equity=Decimal('50000'),          
        retained_earnings=Decimal('5000'),      # 유보율 166% (-1점)
        capital_stock=Decimal('3000'),          
        operating_margin=Decimal('-6')         # 영업이익률 마이너스 (0점)
    )
    
    result = scorer.calculate_total_finance_score(poor_data)
    logger.info(f"취약한 재무상태 테스트 - 점수: {result.total_score}/5 (개별 합계: {result.revenue_growth_score + result.operating_profit_score + result.operating_margin_score + result.retained_earnings_ratio_score + result.debt_ratio_score})")
    
    logger.info("=== 단위 테스트 완료 ===\n")

async def test_api_integration(stock_code: str = "005930"):
    """API 통합 테스트: 실제 KIS API 데이터로 점수 계산"""
    logger.info(f"=== API 통합 테스트: {stock_code} ===")
    
    try:
        import kis_auth as ka
        from dino_test.finance_data_collector import FinanceDataCollector
        from dino_test.finance_scorer import DinoTestFinanceScorer
        
        # KIS API 인증 (실제 토큰 필요)
        try:
            ka.auth(svr="prod", product="01")
            logger.info("✅ KIS API 인증 성공")
        except Exception as e:
            logger.warning(f"⚠️ KIS API 인증 실패: {e} - 데모 모드로 진행")
            return
        
        # 재무 데이터 수집
        collector = FinanceDataCollector()
        finance_data = collector.parse_finance_data(stock_code)
        
        if finance_data is None:
            logger.error(f"❌ 종목 {stock_code}의 재무 데이터 수집 실패")
            return
        
        logger.info(f"✅ 재무 데이터 수집 성공")
        
        # 점수 계산
        scorer = DinoTestFinanceScorer()
        result = scorer.calculate_total_finance_score(finance_data)
        
        # 결과 출력
        logger.info(f"🎯 {stock_code} 디노테스트 재무 점수: {result.total_score}/5점")
        logger.info(f"📊 상세 점수:")
        logger.info(f"   - 매출액 증감: {result.revenue_growth_score}점 ({result.revenue_growth_rate}%)")
        logger.info(f"   - 영업이익 상태: {result.operating_profit_score}점 ({result.operating_profit_transition})")
        logger.info(f"   - 영업이익률: {result.operating_margin_score}점 ({result.operating_margin_rate}%)")
        logger.info(f"   - 유보율: {result.retained_earnings_ratio_score}점 ({result.retained_earnings_ratio}%)")
        logger.info(f"   - 부채비율: {result.debt_ratio_score}점 ({result.debt_ratio}%)")
        
        # 원본 데이터 출력
        logger.info(f"💰 계산에 사용된 실제 데이터:")
        if result.current_period and result.previous_period:
            logger.info(f"   - 기준 기간: {result.current_period} vs {result.previous_period}")
        if result.current_revenue and result.previous_revenue:
            logger.info(f"   - 매출액: {result.current_revenue:,}억 vs {result.previous_revenue:,}억")
        if result.current_operating_profit and result.previous_operating_profit:
            logger.info(f"   - 영업이익: {result.current_operating_profit:,}억 vs {result.previous_operating_profit:,}억")
        if result.total_debt and result.total_equity:
            logger.info(f"   - 부채/자본: {result.total_debt:,}억 / {result.total_equity:,}억")
        if result.retained_earnings and result.capital_stock:
            logger.info(f"   - 이익잉여금/자본금: {result.retained_earnings:,}억 / {result.capital_stock:,}억")
        
        # 통과/불통과 판단 (3점 이상을 통과로 가정)
        if result.total_score >= 3:
            logger.info(f"✅ 디노테스트 통과 ({result.total_score}점 ≥ 3점)")
        else:
            logger.info(f"❌ 디노테스트 불통과 ({result.total_score}점 < 3점)")
            
    except Exception as e:
        logger.error(f"API 통합 테스트 실패: {e}")

async def test_batch_calculation():
    """배치 계산 테스트: 여러 종목 동시 처리"""
    logger.info("=== 배치 계산 테스트 ===")
    
    test_stocks = ["005930", "000660", "035420", "035720", "051910"]  # 삼성전자, SK하이닉스, 네이버, 카카오, LG화학
    
    try:
        import kis_auth as ka
        from dino_test.finance_data_collector import FinanceDataCollector
        from dino_test.finance_scorer import DinoTestFinanceScorer
        
        ka.auth(svr="prod", product="01")
        
        collector = FinanceDataCollector()
        scorer = DinoTestFinanceScorer()
        
        results = []
        
        for stock_code in test_stocks:
            try:
                logger.info(f"처리 중: {stock_code}")
                
                finance_data = collector.parse_finance_data(stock_code)
                if finance_data:
                    result = scorer.calculate_total_finance_score(finance_data)
                    results.append({
                        "stock_code": stock_code,
                        "total_score": result.total_score,
                        "passed": result.total_score >= 3
                    })
                    logger.info(f"{stock_code}: {result.total_score}점 ({'통과' if result.total_score >= 3 else '불통과'})")
                else:
                    logger.warning(f"{stock_code}: 데이터 수집 실패")
                    
            except Exception as e:
                logger.error(f"{stock_code} 처리 중 오류: {e}")
        
        # 통계
        if results:
            scores = [r["total_score"] for r in results]
            passed_count = len([r for r in results if r["passed"]])
            
            logger.info(f"📊 배치 계산 결과:")
            logger.info(f"   - 처리된 종목: {len(results)}개")
            logger.info(f"   - 평균 점수: {sum(scores) / len(scores):.2f}점")
            logger.info(f"   - 통과 종목: {passed_count}개 ({passed_count/len(results)*100:.1f}%)")
            logger.info(f"   - 최고/최저 점수: {max(scores)}점 / {min(scores)}점")
            
    except Exception as e:
        logger.error(f"배치 계산 테스트 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description="디노테스트 재무 점수 계산 테스트")
    parser.add_argument("--stock-code", default="005930", help="테스트할 종목코드 (기본: 005930)")
    parser.add_argument("--unit-test", action="store_true", help="단위 테스트만 실행")
    parser.add_argument("--api-test", action="store_true", help="API 통합 테스트만 실행")
    parser.add_argument("--batch", action="store_true", help="배치 계산 테스트 실행")
    
    args = parser.parse_args()
    
    if args.unit_test:
        test_finance_scorer_unit()
    elif args.api_test:
        asyncio.run(test_api_integration(args.stock_code))
    elif args.batch:
        asyncio.run(test_batch_calculation())
    else:
        # 전체 테스트 실행
        logger.info("🚀 디노테스트 재무 점수 계산기 전체 테스트 시작")
        test_finance_scorer_unit()
        asyncio.run(test_api_integration(args.stock_code))
        
        if input("배치 테스트를 실행하시겠습니까? (y/N): ").lower() == 'y':
            asyncio.run(test_batch_calculation())
        
        logger.info("✅ 모든 테스트 완료!")

if __name__ == "__main__":
    main()