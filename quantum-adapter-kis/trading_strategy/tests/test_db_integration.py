#!/usr/bin/env python3
"""
데이터베이스 연동 테스트
기존 JSON 분석 결과를 PostgreSQL에 저장하고 조회 테스트

Author: Quantum Trading Platform
Created: 2025-09-04
"""

import json
import logging
from pathlib import Path
from datetime import datetime

# 현재 폴더 경로 추가
import sys
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from db_manager import DatabaseManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def test_db_connection():
    """데이터베이스 연결 테스트"""
    logger.info("🔌 데이터베이스 연결 테스트...")
    
    db = DatabaseManager()
    if db.connection:
        logger.info("✅ 데이터베이스 연결 성공!")
        return db
    else:
        logger.error("❌ 데이터베이스 연결 실패!")
        return None

def load_json_analysis():
    """기존 JSON 분석 결과 로드"""
    json_file = current_dir / "analysis_results" / "comprehensive_analysis_20250904.json"
    
    if not json_file.exists():
        logger.error(f"❌ JSON 파일을 찾을 수 없습니다: {json_file}")
        return None
    
    logger.info(f"📄 JSON 파일 로드 중: {json_file}")
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    logger.info(f"✅ JSON 로드 완료: {data['analysis_info']['total_stocks']}개 종목")
    return data

def test_data_insertion(db: DatabaseManager, analysis_data: dict):
    """데이터 삽입 테스트"""
    logger.info("💾 데이터베이스 저장 테스트...")
    
    # 분석 결과 저장
    success = db.save_analysis_result(analysis_data)
    
    if success:
        logger.info("✅ 데이터 저장 성공!")
        return True
    else:
        logger.error("❌ 데이터 저장 실패!")
        return False

def test_data_query(db: DatabaseManager):
    """데이터 조회 테스트"""
    logger.info("🔍 데이터 조회 테스트...")
    
    # 최근 분석 결과 조회 (TOP 10)
    latest_analysis = db.get_latest_analysis(10)
    if latest_analysis:
        logger.info(f"📊 최근 분석 결과 TOP 10:")
        for i, stock in enumerate(latest_analysis, 1):
            logger.info(f"  {i:2d}. {stock['symbol']:8s} | {stock['investment_score']:5.1f}점 | {stock['recommendation']:8s} | {stock['current_price']:>10} | RSI {stock['rsi']:5.1f}")
    
    # 분석 요약 조회
    summary = db.get_analysis_summary()
    if summary:
        logger.info(f"📈 분석 요약:")
        logger.info(f"  - 총 분석 종목: {summary.get('total_stocks', 0)}개")
        logger.info(f"  - 평균 점수: {summary.get('total_avg_score', 0):.1f}점")
        logger.info(f"  - 매수 추천: {summary.get('buy_recommend_count', 0)}개")
        logger.info(f"  - 국내 종목: {summary.get('domestic_count', 0)}개 (평균 {summary.get('domestic_avg_score', 0):.1f}점)")
        logger.info(f"  - 해외 종목: {summary.get('overseas_count', 0)}개 (평균 {summary.get('overseas_avg_score', 0):.1f}점)")

def main():
    """메인 테스트 함수"""
    logger.info("🚀 PostgreSQL 연동 테스트 시작")
    
    # 1. DB 연결 테스트
    db = test_db_connection()
    if not db:
        return
    
    # 2. JSON 데이터 로드
    analysis_data = load_json_analysis()
    if not analysis_data:
        return
    
    # 3. 데이터 삽입 테스트
    if test_data_insertion(db, analysis_data):
        # 4. 데이터 조회 테스트
        test_data_query(db)
    
    # 5. 연결 해제
    db.disconnect()
    logger.info("🎉 테스트 완료!")

if __name__ == "__main__":
    main()