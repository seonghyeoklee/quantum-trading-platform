#!/usr/bin/env python3
"""
VectorBT 성능 테스트 및 Backtrader와의 비교
고성능 백테스팅 라이브러리의 성능과 정확성을 검증
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import time
import warnings

# 프로젝트 경로 추가
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

# 경고 메시지 무시
warnings.filterwarnings('ignore')

# VectorBT는 Python 3.13을 지원하지 않으므로 numpy 벡터화 연산으로 대체
VECTORBT_AVAILABLE = False
print("ℹ️ VectorBT는 Python 3.13 미지원 - numpy 벡터화 연산으로 테스트")

from core.multi_data_provider import MultiDataProvider, DataSource
from core.backtester import GoldenCrossBacktester

def prepare_test_data():
    """테스트 데이터 준비"""
    print("📊 테스트 데이터 준비 중...")
    
    provider = MultiDataProvider(enable_kis=False, cache_enabled=True)
    symbols = ["005930", "035720"]  # 삼성전자, 카카오
    
    data = {}
    for symbol in symbols:
        result = provider.get_stock_data(
            symbol,
            datetime.now() - timedelta(days=100),
            datetime.now(),
            DataSource.AUTO
        )
        if result:
            data[symbol] = result.data
            print(f"✅ {symbol}: {len(result.data)}일 데이터 로드")
        else:
            print(f"❌ {symbol}: 데이터 로드 실패")
    
    return data

def calculate_moving_averages(df):
    """이동평균 계산"""
    df = df.copy()
    df['SMA5'] = df['Close'].rolling(window=5).mean()
    df['SMA20'] = df['Close'].rolling(window=20).mean()
    return df

def test_numpy_vectorized_golden_cross(symbol, df, confirmation_days=1):
    """Numpy 벡터화 연산을 이용한 고성능 골든크로스 백테스팅"""
    print(f"\n🔥 Numpy 벡터화 골든크로스 테스트: {symbol} (확정: {confirmation_days}일)")
    
    start_time = time.time()
    
    # 이동평균 계산 (numpy 벡터화 연산)
    df_with_ma = calculate_moving_averages(df)
    
    # numpy 배열로 변환 (성능 향상)
    close_prices = df_with_ma['Close'].values
    sma5 = df_with_ma['SMA5'].values
    sma20 = df_with_ma['SMA20'].values
    
    # 골든크로스/데드크로스 시그널 생성 (벡터화)
    golden_cross = (sma5 > sma20) & (np.roll(sma5, 1) <= np.roll(sma20, 1))
    dead_cross = (sma5 < sma20) & (np.roll(sma5, 1) >= np.roll(sma20, 1))
    
    # 확정 기간 적용 (벡터화된 연속 조건 확인)
    if confirmation_days > 1:
        for i in range(1, confirmation_days):
            if i < len(sma5):
                golden_cross = golden_cross & (np.roll(sma5, -i) > np.roll(sma20, -i))
                dead_cross = dead_cross & (np.roll(sma5, -i) < np.roll(sma20, -i))
    
    # 포지션 생성 (1: 매수, -1: 매도, 0: 중립)
    positions = np.zeros(len(close_prices))
    positions[golden_cross] = 1
    positions[dead_cross] = -1
    
    # 포지션 전파 (ffill 효과)
    for i in range(1, len(positions)):
        if positions[i] == 0:
            positions[i] = positions[i-1]
    
    # 포트폴리오 계산 (벡터화된 연산)
    initial_cash = 10_000_000
    returns = np.diff(close_prices) / close_prices[:-1]
    portfolio_returns = returns * positions[:-1]  # 포지션에 따른 수익률
    
    # 누적 수익률 계산
    cumulative_returns = np.cumprod(1 + portfolio_returns) 
    final_value = initial_cash * cumulative_returns[-1] if len(cumulative_returns) > 0 else initial_cash
    total_return = (final_value - initial_cash) / initial_cash
    
    # 거래 횟수 계산
    position_changes = np.diff(positions)
    trades_count = np.sum(np.abs(position_changes) > 0)
    
    # 승률 계산 (양수 수익률의 비율)
    win_count = np.sum(portfolio_returns > 0)
    total_trades = np.sum(portfolio_returns != 0)
    win_rate = win_count / total_trades if total_trades > 0 else 0
    
    # 최대손실 계산
    cumulative_value = initial_cash * cumulative_returns
    peak = np.maximum.accumulate(cumulative_value)
    drawdown = (cumulative_value - peak) / peak
    max_drawdown = np.abs(np.min(drawdown)) if len(drawdown) > 0 else 0
    
    # 샤프 비율 계산 (간단한 버전)
    if np.std(portfolio_returns) > 0:
        sharpe_ratio = np.mean(portfolio_returns) / np.std(portfolio_returns) * np.sqrt(252)
    else:
        sharpe_ratio = 0
    
    calculation_time = time.time() - start_time
    
    result = {
        'symbol': symbol,
        'confirmation_days': confirmation_days,
        'total_return': total_return,
        'win_rate': win_rate,
        'max_drawdown': max_drawdown,
        'sharpe_ratio': sharpe_ratio,
        'trades_count': trades_count,
        'calculation_time': calculation_time,
        'final_value': final_value
    }
    
    print(f"  💰 수익률: {total_return*100:+.2f}%")
    print(f"  🎯 승률: {win_rate*100:.1f}%")
    print(f"  📉 최대손실: {max_drawdown*100:.2f}%")
    print(f"  📊 샤프비율: {sharpe_ratio:.3f}")
    print(f"  🔄 거래횟수: {trades_count}")
    print(f"  ⚡ 계산시간: {calculation_time:.3f}초")
    
    return result

def test_backtrader_golden_cross(symbol, df, confirmation_days=1):
    """기존 Backtrader를 이용한 골든크로스 백테스팅"""
    print(f"\n📈 Backtrader 골든크로스 테스트: {symbol} (확정: {confirmation_days}일)")
    
    start_time = time.time()
    
    # 백테스터 실행
    backtester = GoldenCrossBacktester()
    
    # 컬럼명을 소문자로 변환 (Backtrader 요구사항)
    df_bt = df.copy()
    df_bt.columns = [col.lower() for col in df_bt.columns]
    
    # Backtrader 데이터 형식으로 변환
    bt_data = backtester.prepare_data(df_bt, symbol)
    
    results = backtester.run_single_test(
        data=bt_data,
        symbol=symbol,
        symbol_name=f"종목{symbol}",
        confirmation_days=confirmation_days
    )
    
    calculation_time = time.time() - start_time
    
    if results:
        print(f"  💰 수익률: {results['return_pct']:+.2f}%")
        print(f"  💵 최종금액: {results['final_value']:,.0f}원")
        print(f"  🔄 거래횟수: {results['total_trades']}")
        print(f"  ⚡ 계산시간: {calculation_time:.3f}초")
        
        return {
            'symbol': symbol,
            'confirmation_days': confirmation_days,
            'total_return': results['return_pct'] / 100,
            'final_value': results['final_value'],
            'trades_count': results['total_trades'],
            'calculation_time': calculation_time
        }
    else:
        print("  ❌ 백테스트 실패")
        return None

def performance_comparison():
    """VectorBT vs Backtrader 성능 비교"""
    print("=" * 70)
    print("⚡ VectorBT vs Backtrader 성능 비교")
    print("=" * 70)
    
    # 테스트 데이터 준비
    data = prepare_test_data()
    
    if not data:
        print("❌ 테스트 데이터 없음")
        return
    
    comparison_results = []
    
    for symbol, df in data.items():
        print(f"\n🏢 {symbol} 종목 비교 테스트")
        print("-" * 50)
        
        for confirmation_days in [1, 3, 7]:
            print(f"\n📅 확정기간: {confirmation_days}일")
            
            # Numpy 벡터화 테스트
            numpy_result = None
            try:
                numpy_result = test_numpy_vectorized_golden_cross(symbol, df, confirmation_days)
            except Exception as e:
                print(f"❌ Numpy 벡터화 테스트 실패: {e}")
            
            # Backtrader 테스트
            bt_result = None
            try:
                bt_result = test_backtrader_golden_cross(symbol, df, confirmation_days)
            except Exception as e:
                print(f"❌ Backtrader 테스트 실패: {e}")
            
            # 결과 비교
            if numpy_result and bt_result:
                speed_improvement = (bt_result['calculation_time'] - numpy_result['calculation_time']) / bt_result['calculation_time'] * 100
                
                comparison = {
                    'symbol': symbol,
                    'confirmation_days': confirmation_days,
                    'numpy_vectorized': numpy_result,
                    'backtrader': bt_result,
                    'speed_improvement': speed_improvement
                }
                comparison_results.append(comparison)
                
                print(f"\n⚡ 성능 비교:")
                print(f"  Numpy 벡터화: {numpy_result['calculation_time']:.3f}초")
                print(f"  Backtrader:   {bt_result['calculation_time']:.3f}초")
                print(f"  성능향상:     {speed_improvement:+.1f}%")
    
    # 종합 결과
    if comparison_results:
        print("\n" + "=" * 70)
        print("📊 종합 성능 비교 결과")
        print("=" * 70)
        
        total_numpy_time = sum([r['numpy_vectorized']['calculation_time'] for r in comparison_results if 'numpy_vectorized' in r])
        total_bt_time = sum([r['backtrader']['calculation_time'] for r in comparison_results if 'backtrader' in r])
        overall_improvement = (total_bt_time - total_numpy_time) / total_bt_time * 100 if total_bt_time > 0 else 0
        
        print(f"📈 총 테스트 케이스: {len(comparison_results)}개")
        print(f"⚡ Numpy 벡터화 총 시간: {total_numpy_time:.3f}초")
        print(f"⚡ Backtrader 총 시간: {total_bt_time:.3f}초")
        print(f"🚀 전체 성능 향상: {overall_improvement:+.1f}%")
        
        # 상세 비교표
        print(f"\n📋 상세 비교:")
        print(f"{'종목':<8} {'확정':<4} {'Numpy수익':<12} {'Backtrader수익':<14} {'시간비교':<10}")
        print("-" * 60)
        
        for r in comparison_results:
            numpy_return = r['numpy_vectorized']['total_return'] * 100
            bt_return = r['backtrader']['total_return'] * 100
            time_ratio = r['numpy_vectorized']['calculation_time'] / r['backtrader']['calculation_time']
            
            print(f"{r['symbol']:<8} {r['confirmation_days']:>2}일 {numpy_return:>+8.2f}%    {bt_return:>+8.2f}%     {time_ratio:.2f}배")

def numpy_advanced_features():
    """Numpy 벡터화 고급 기능 테스트"""
    print("\n" + "=" * 70)
    print("🔬 Numpy 벡터화 고급 기능 테스트")
    print("=" * 70)
    
    # 테스트 데이터 준비
    data = prepare_test_data()
    if not data:
        return
    
    symbol = "005930"
    df = data[symbol]
    df_with_ma = calculate_moving_averages(df)
    
    print(f"\n📊 {symbol} 고급 분석")
    
    # 다중 확정 기간 동시 테스트
    confirmation_periods = [1, 2, 3, 5, 7]
    
    print(f"\n🔥 다중 확정기간 벡터화 테스트 ({len(confirmation_periods)}개 동시)")
    start_time = time.time()
    
    # numpy 배열로 변환
    close_prices = df_with_ma['Close'].values
    sma5_values = df_with_ma['SMA5'].values
    sma20_values = df_with_ma['SMA20'].values
    
    results = {}
    for days in confirmation_periods:
        # 골든크로스/데드크로스 시그널 생성 (벡터화)
        golden_cross = (sma5_values > sma20_values) & (np.roll(sma5_values, 1) <= np.roll(sma20_values, 1))
        dead_cross = (sma5_values < sma20_values) & (np.roll(sma5_values, 1) >= np.roll(sma20_values, 1))
        
        # 확정 기간 적용 (벡터화된 연속 조건 확인)
        if days > 1:
            for i in range(1, days):
                if i < len(sma5_values):
                    golden_cross = golden_cross & (np.roll(sma5_values, -i) > np.roll(sma20_values, -i))
                    dead_cross = dead_cross & (np.roll(sma5_values, -i) < np.roll(sma20_values, -i))
        
        # 포지션 생성 및 수익률 계산
        positions = np.zeros(len(close_prices))
        positions[golden_cross] = 1
        positions[dead_cross] = -1
        
        # 포지션 전파
        for i in range(1, len(positions)):
            if positions[i] == 0:
                positions[i] = positions[i-1]
        
        # 수익률 계산
        returns = np.diff(close_prices) / close_prices[:-1]
        portfolio_returns = returns * positions[:-1]
        
        if len(portfolio_returns) > 0:
            cumulative_returns = np.cumprod(1 + portfolio_returns)
            total_return = cumulative_returns[-1] - 1
            
            # 거래 횟수 계산
            position_changes = np.diff(positions)
            trades_count = np.sum(np.abs(position_changes) > 0)
            
            # 승률 계산
            win_count = np.sum(portfolio_returns > 0)
            total_trades = np.sum(portfolio_returns != 0)
            win_rate = win_count / total_trades if total_trades > 0 else 0
        else:
            total_return = 0
            trades_count = 0
            win_rate = 0
        
        results[f"{days}일"] = {
            'return': total_return,
            'trades': trades_count,
            'win_rate': win_rate
        }
    
    vectorized_time = time.time() - start_time
    
    print(f"✅ 벡터화 계산 완료: {vectorized_time:.3f}초")
    print(f"\n📋 다중 확정기간 결과:")
    for period, result in results.items():
        print(f"  {period:<4}: 수익률 {result['return']*100:+6.2f}%, 거래 {result['trades']:2.0f}회, 승률 {result['win_rate']*100:5.1f}%")

if __name__ == "__main__":
    print("🚀 Numpy 벡터화 vs Backtrader 성능 테스트 시작")
    
    # 성능 비교 테스트
    performance_comparison()
    
    # 고급 기능 테스트
    numpy_advanced_features()
    
    print("\n✅ 고성능 백테스팅 라이브러리 비교 테스트 완료!")
    
    print("\n💡 향후 계획:")
    print("- VectorBT: Python 3.10 이하 환경에서 사용 가능한 고성능 백테스팅")
    print("- TA-Lib: 기술적 지표 라이브러리 추가 (별도 설치)")
    print("- Numpy 벡터화: 현재 환경에서 최적의 성능 달성")