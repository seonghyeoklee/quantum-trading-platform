#!/usr/bin/env python3
"""
골든크로스 백테스팅 시스템 (Backtrader 기반)
종목별 최적 확정 기간 분석 및 전문 백테스팅
"""

import asyncio
import sys
import logging
from pathlib import Path
from datetime import datetime
import pandas as pd

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))
sys.path.append(str(current_dir.parent / 'examples_llm'))

# KIS API 모듈 import
import kis_auth as ka
from domestic_stock.inquire_daily_itemchartprice.inquire_daily_itemchartprice import inquire_daily_itemchartprice

# trading_strategy 모듈 import
from core.backtester import GoldenCrossBacktester, convert_kis_data

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# 테스트할 종목 리스트
TEST_SYMBOLS = {
    # 대형주 & IT
    "005930": "삼성전자",
    "035720": "카카오",
    
    # 조선 테마  
    "009540": "HD한국조선해양",
    
    # 방산 테마
    "012450": "한화에어로스페이스",
    
    # 원자력 테마
    "010060": "OCI"
}

def get_stock_data(symbol: str) -> pd.DataFrame:
    """
    KIS API에서 종목 데이터 조회 (150일)
    """
    try:
        logger.info(f"📊 {symbol} 데이터 수집 중...")
        
        # 날짜 범위 설정 (최근 150일)
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=150)).strftime("%Y%m%d")
        
        output1, output2 = inquire_daily_itemchartprice(
            env_dv="real",
            fid_cond_mrkt_div_code="J",  # KRX
            fid_input_iscd=symbol,
            fid_input_date_1=start_date,  # 시작 날짜
            fid_input_date_2=end_date,    # 종료 날짜  
            fid_period_div_code="D",      # 일봉
            fid_org_adj_prc="1"           # 원주가
        )
        
        if output2.empty:
            logger.error(f"❌ {symbol}: 데이터가 없습니다")
            return None
        
        # Backtrader 형식으로 변환
        df = convert_kis_data(output2)
        
        logger.info(f"✅ {symbol}: {len(df)}일 데이터 수집 완료")
        return df
        
    except Exception as e:
        logger.error(f"❌ {symbol} 데이터 수집 실패: {e}")
        return None

async def run_backtest():
    """골든크로스 백테스팅 시스템 실행"""
    print("\n" + "="*70)
    print("🚀 골든크로스 백테스팅 시스템 (Backtrader)")
    print("="*70)
    print(f"📅 테스트 기간: 최근 150일")
    print(f"📊 테스트 종목: {len(TEST_SYMBOLS)}개")
    print(f"⚙️  확정 기간: 1일, 2일, 3일, 5일, 7일")
    print(f"💰 초기 자금: 1,000만원")
    print(f"🔧 엔진: Backtrader (전문 백테스팅 라이브러리)")
    print("="*70)
    
    # KIS API 인증
    logger.info("🔐 KIS API 인증 시작...")
    ka.auth()
    logger.info("✅ KIS API 인증 성공")
    
    # 백테스터 초기화
    backtester = GoldenCrossBacktester(initial_cash=10_000_000, commission=0.00015)
    
    # 전체 결과 저장
    all_results = {}
    summary_results = []
    
    # 각 종목별 백테스팅 실행
    for symbol, name in TEST_SYMBOLS.items():
        try:
            # 데이터 수집
            data = get_stock_data(symbol)
            if data is None or len(data) < 50:
                logger.warning(f"⚠️ {name}({symbol}): 데이터 부족으로 스킵")
                continue
            
            # 확정 기간별 백테스팅
            results = backtester.compare_confirmation_periods(data, symbol, name)
            all_results[symbol] = results
            
            # 결과 출력
            backtester.print_comparison_table(results)
            
            # 최적 결과 요약에 추가
            if results:
                best_period = max(results.keys(), key=lambda k: results[k]['total_return'])
                best_result = results[best_period]
                
                summary_results.append({
                    'symbol': symbol,
                    'name': name,
                    'optimal_days': best_period,
                    'return': best_result['total_return'],
                    'initial': best_result['initial_value'],
                    'final': best_result['final_value']
                })
                
                # 각 종목별 최적 결과 간단 출력
                print(f"🏆 {name}: {best_period}일 확정 "
                      f"(수익률: {best_result['total_return']:+.2f}%)")
            
        except Exception as e:
            logger.error(f"❌ {name}({symbol}) 백테스팅 실패: {e}")
            continue
    
    # 전체 요약 결과 출력
    print_detailed_summary(all_results, summary_results)
    
    return all_results, summary_results

def print_detailed_summary(all_results: dict, summary_results: list):
    """상세 요약 결과 출력"""
    if not summary_results:
        print("❌ 백테스팅 결과가 없습니다.")
        return
    
    print("\n" + "="*90)
    print("🏆 전체 백테스팅 상세 요약 결과 (전문 백테스터)")
    print("="*90)
    print(f"{'종목명':<15} {'코드':<8} {'최적확정':<8} {'수익률':<10} {'초기자금':<12} {'최종자금':<12}")
    print("-"*90)
    
    total_return_sum = 0
    positive_count = 0
    
    # 수익률 순으로 정렬
    sorted_results = sorted(summary_results, key=lambda x: x['return'], reverse=True)
    
    for result in sorted_results:
        print(f"{result['name']:<15} {result['symbol']:<8} "
              f"{result['optimal_days']}일{'':<5} {result['return']:+7.2f}%   "
              f"{result['initial']:>10,.0f}원   {result['final']:>10,.0f}원")
        
        total_return_sum += result['return']
        if result['return'] > 0:
            positive_count += 1
    
    print("-"*90)
    print(f"📊 전체 통계:")
    print(f"  - 평균 수익률: {total_return_sum/len(summary_results):+.2f}%")
    print(f"  - 수익 종목: {positive_count}/{len(summary_results)}개 ({positive_count/len(summary_results)*100:.1f}%)")
    
    # 확정 기간별 통계
    period_stats = {}
    for result in summary_results:
        period = result['optimal_days']
        if period not in period_stats:
            period_stats[period] = 0
        period_stats[period] += 1
    
    print(f"  - 최적 확정 기간 분포:")
    for period in sorted(period_stats.keys()):
        count = period_stats[period]
        print(f"    {period}일: {count}개 종목 ({count/len(summary_results)*100:.1f}%)")
    
    # 확정 기간별 차이점 분석
    print(f"\n🔍 확정 기간별 차이점 분석:")
    
    for symbol, results in all_results.items():
        if len(results) < 2:
            continue
            
        symbol_info = next(r for r in summary_results if r['symbol'] == symbol)
        name = symbol_info['name']
        
        # 1일 vs 최적 기간 비교
        period_1 = results.get(1)
        best_period = symbol_info['optimal_days']
        best_result = results.get(best_period)
        
        if period_1 and best_result and best_period != 1:
            diff = best_result['total_return'] - period_1['total_return']
            print(f"  - {name}: 1일({period_1['total_return']:+.2f}%) vs "
                  f"{best_period}일({best_result['total_return']:+.2f}%) = "
                  f"{diff:+.2f}%p 차이")
        elif period_1 and best_period == 1:
            print(f"  - {name}: 1일 확정이 최적 ({period_1['total_return']:+.2f}%)")

if __name__ == "__main__":
    try:
        # 골든크로스 백테스팅 실행
        results, summary = asyncio.run(run_backtest())
        
        print("\n✅ 골든크로스 백테스팅 완료!")
        print("\n💡 이제 확정 기간별로 실제 차이를 확인할 수 있습니다:")
        print("  1. 각 종목별 최적 확정 기간 도출")
        print("  2. 1일 vs 3일 vs 5일 vs 7일의 실제 수익률 차이 분석")
        print("  3. 확정 기간이 길수록 안전하지만 수익률 감소 패턴 확인")
        
    except KeyboardInterrupt:
        print("\n🛑 백테스팅이 중지되었습니다.")
    except Exception as e:
        logger.error(f"❌ 백테스팅 실행 중 오류: {e}")
        sys.exit(1)