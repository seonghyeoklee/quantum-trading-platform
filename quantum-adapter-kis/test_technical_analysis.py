#!/usr/bin/env python3
"""
디노테스트 기술분석 테스트 스크립트

Usage:
    python test_technical_analysis.py
    python test_technical_analysis.py --stock-code=005930
"""

import asyncio
import argparse
import logging
import sys

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 경로 설정
sys.path.extend(['.', 'examples_llm'])

async def test_technical_analysis(stock_code: str = "005930"):
    """기술분석 테스트: 실제 KIS API 데이터로 OBV, RSI 계산"""
    logger.info(f"=== 기술분석 테스트: {stock_code} ===")
    
    try:
        import kis_auth as ka
        from dino_test.technical_data_collector import TechnicalDataCollector
        from dino_test.technical_analyzer import DinoTestTechnicalAnalyzer
        
        # KIS API 인증
        try:
            ka.auth(svr="prod", product="01")
            logger.info("✅ KIS API 인증 성공")
        except Exception as e:
            logger.warning(f"⚠️ KIS API 인증 실패: {e}")
            return
        
        # 기술분석 데이터 수집
        collector = TechnicalDataCollector()
        technical_data = collector.collect_technical_analysis_data(stock_code)
        
        if technical_data is None:
            logger.error(f"❌ 종목 {stock_code}의 기술분석 데이터 수집 실패")
            return
        
        logger.info(f"✅ 기술분석 데이터 수집 성공")
        
        # 기술분석 점수 계산
        analyzer = DinoTestTechnicalAnalyzer()
        result = analyzer.calculate_total_technical_score(technical_data)
        
        # 결과 출력
        logger.info(f"🎯 {stock_code} 디노테스트 기술분석 점수: {result.total_score}/4점")
        logger.info(f"📊 상세 점수:")
        logger.info(f"   - OBV: {result.obv_score}점 ({result.obv_status})")
        logger.info(f"   - RSI: {result.rsi_score}점 (RSI: {result.rsi_value:.2f})")
        logger.info(f"   - 투자심리: {result.sentiment_score}점 (미구현)")
        logger.info(f"   - 기타지표: {result.other_indicator_score}점 (미구현)")
        
        # 계산 근거 출력
        logger.info(f"💰 계산에 사용된 데이터:")
        if result.obv_change_rate is not None:
            logger.info(f"   - OBV 2년 변화율: {result.obv_change_rate:.2f}%")
        if result.price_change_rate is not None:
            logger.info(f"   - 주가 2년 변화율: {result.price_change_rate:.2f}%")
        if result.rsi_value is not None:
            logger.info(f"   - 현재 RSI: {result.rsi_value:.2f}")
        
        # 차트 데이터 정보
        if technical_data.chart_data is not None:
            chart_info = technical_data.chart_data
            logger.info(f"   - 차트 데이터: {len(chart_info)}일 ({chart_info['date'].min().strftime('%Y-%m-%d')} ~ {chart_info['date'].max().strftime('%Y-%m-%d')})")
            
    except Exception as e:
        logger.error(f"기술분석 테스트 실패: {e}")

def main():
    parser = argparse.ArgumentParser(description="디노테스트 기술분석 테스트")
    parser.add_argument("--stock-code", default="005930", help="테스트할 종목코드 (기본: 005930)")
    
    args = parser.parse_args()
    
    logger.info("🚀 디노테스트 기술분석 테스트 시작")
    asyncio.run(test_technical_analysis(args.stock_code))
    logger.info("✅ 기술분석 테스트 완료!")

if __name__ == "__main__":
    main()