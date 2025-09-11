#!/usr/bin/env python3
"""
DINO Test 재료 영역 분석 테스트 스크립트

재료 영역 4개 지표를 실제 KIS API 데이터로 테스트합니다:
1. 고배당 (2% 이상) (±1점)
2. 기관/외국인 수급 (최근 1~3개월, 상장주식수의 1% 이상) (±1점) 
3. 어닝서프라이즈 (컨센서스 대비 10% 이상) (±1점) - 향후 구현
4. 기타 소재 항목들 (뉴스, 이벤트 등) - 향후 구현

사용법:
  python test_dino_material.py                    # 기본 테스트 (삼성전자)
  python test_dino_material.py 005930             # 특정 종목
  python test_dino_material.py 005930 --verbose   # 상세 출력
"""

import sys
import logging
import argparse
from typing import Optional
from datetime import datetime

# 경로 설정
sys.path.extend(['..', '.'])

# DINO Test 재료 모듈
from dino_test.material_data_collector import MaterialDataCollector
from dino_test.material_analyzer import DinoTestMaterialAnalyzer, MaterialScoreDetail

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dino_material_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class DinoMaterialTester:
    """DINO Test 재료 영역 테스트 클래스"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.collector = MaterialDataCollector()
        self.analyzer = DinoTestMaterialAnalyzer()
        
        # 로그 레벨 조정
        if not verbose:
            logging.getLogger('dino_test.material_data_collector').setLevel(logging.WARNING)
            logging.getLogger('dino_test.material_analyzer').setLevel(logging.WARNING)
    
    def test_single_stock(self, stock_code: str) -> Optional[MaterialScoreDetail]:
        """단일 종목 재료 분석 테스트"""
        
        logger.info(f"=" * 60)
        logger.info(f"DINO Test 재료 영역 분석 - 종목: {stock_code}")
        logger.info(f"=" * 60)
        
        try:
            # KIS API 인증 (실제 토큰 필요)
            import kis_auth as ka
            try:
                ka.auth(svr="prod", product="01")
                logger.info("✅ KIS API 인증 성공")
            except Exception as e:
                logger.warning(f"⚠️ KIS API 인증 실패: {e} - 데모 모드로 진행")
                # 인증 실패 시에도 계속 진행 (기본값으로 처리)
            # 1. 재료 데이터 수집
            logger.info("📊 1단계: 재료 데이터 수집 중...")
            material_data = self.collector.collect_material_analysis_data(stock_code)
            
            if material_data is None:
                logger.error(f"❌ 재료 데이터 수집 실패 - {stock_code}")
                return None
            
            # 2. 재료 점수 계산
            logger.info("🎯 2단계: 재료 점수 계산 중...")
            score_detail = self.analyzer.calculate_total_material_score(material_data)
            
            # 3. 결과 출력
            self._print_results(stock_code, score_detail)
            
            return score_detail
            
        except Exception as e:
            logger.error(f"❌ 재료 분석 실패 - {stock_code}: {e}")
            if self.verbose:
                import traceback
                logger.error(traceback.format_exc())
            return None
    
    def _print_results(self, stock_code: str, score_detail: MaterialScoreDetail):
        """분석 결과 출력"""
        
        print(f"\n🎯 DINO Test 재료 영역 분석 결과 - {stock_code}")
        print("=" * 50)
        
        # 총점
        total_score = score_detail.total_score
        print(f"📊 재료 영역 총점: {total_score}/5점")
        
        if total_score >= 4:
            score_grade = "우수"
            score_emoji = "🟢"
        elif total_score >= 3:
            score_grade = "양호" 
            score_emoji = "🟡"
        elif total_score >= 2:
            score_grade = "보통"
            score_emoji = "🟠"
        else:
            score_grade = "미흡"
            score_emoji = "🔴"
        
        print(f"{score_emoji} 평가: {score_grade}")
        print()
        
        # 세부 점수 분석
        print("📈 세부 점수 분석:")
        print(f"  • D004 고배당 분석: {score_detail.dividend_score}/1점")
        if score_detail.dividend_status:
            print(f"    └─ {score_detail.dividend_status}")
        
        print(f"  • D003 기관 수급: {score_detail.institutional_score}/1점")
        if score_detail.institutional_status:
            print(f"    └─ {score_detail.institutional_status}")
        
        print(f"  • D003 외국인 수급: {score_detail.foreign_score}/1점")
        if score_detail.foreign_status:
            print(f"    └─ {score_detail.foreign_status}")
        
        print(f"  • D005 어닝서프라이즈: {score_detail.earnings_surprise_score}/1점")
        print(f"    └─ 향후 구현 예정")
        
        print()
        
        # 투자 시사점
        print("💡 투자 시사점:")
        
        # 배당 관련 시사점
        if score_detail.dividend_score > 0:
            print("  ✅ 고배당주로 안정적 수익 기대")
        else:
            print("  ⚠️  배당 수익성 낮음")
        
        # 수급 관련 시사점
        supply_score = score_detail.institutional_score + score_detail.foreign_score
        if supply_score >= 2:
            print("  ✅ 기관/외국인 동반 매집, 강한 상승 동력")
        elif supply_score >= 1:
            print("  🟡 기관 또는 외국인 매집, 제한적 상승 동력")
        else:
            print("  ⚠️  기관/외국인 수급 부진")
        
        print()
        
        # 상세 데이터 (verbose 모드)
        if self.verbose:
            print("📊 상세 데이터:")
            if score_detail.dividend_yield is not None:
                print(f"  • 배당률: {score_detail.dividend_yield:.2f}%")
            if score_detail.institutional_ratio is not None:
                print(f"  • 기관 보유비율: {score_detail.institutional_ratio:.2f}%")
            if score_detail.foreign_ratio is not None:
                print(f"  • 외국인 보유비율: {score_detail.foreign_ratio:.2f}%")
            if score_detail.institutional_change is not None:
                print(f"  • 기관 변화율: {score_detail.institutional_change:.2f}%")
            if score_detail.foreign_change is not None:
                print(f"  • 외국인 변화율: {score_detail.foreign_change:.2f}%")
            print()

def main():
    """메인 실행 함수"""
    
    parser = argparse.ArgumentParser(
        description="DINO Test 재료 영역 분석 테스트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python test_dino_material.py                    # 기본 테스트 (삼성전자)
  python test_dino_material.py 005930             # 삼성전자 분석
  python test_dino_material.py 000660             # SK하이닉스 분석  
  python test_dino_material.py 035720 --verbose   # 카카오 상세 분석

테스트 종목 추천:
  005930 - 삼성전자 (대형주, 고배당)
  000660 - SK하이닉스 (반도체, 외국인 선호)
  035720 - 카카오 (성장주)
  003550 - LG (고배당, 기관 선호)
  068270 - 셀트리온 (바이오, 외국인 관심)
        """
    )
    
    parser.add_argument(
        'stock_code', 
        nargs='?', 
        default='005930',
        help='분석할 종목코드 (기본값: 005930 삼성전자)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='상세 출력 모드'
    )
    
    args = parser.parse_args()
    
    # 종목코드 검증
    stock_code = args.stock_code.zfill(6)  # 6자리로 패딩
    
    print(f"🚀 DINO Test 재료 영역 분석 시작")
    print(f"📅 실행시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 대상종목: {stock_code}")
    if args.verbose:
        print(f"🔍 상세모드: 활성화")
    print()
    
    # 테스터 실행
    tester = DinoMaterialTester(verbose=args.verbose)
    result = tester.test_single_stock(stock_code)
    
    if result:
        print("✅ 재료 분석 완료")
        print(f"📝 로그 파일: dino_material_test.log")
    else:
        print("❌ 재료 분석 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()