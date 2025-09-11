"""
디노테스트 기술분석 데이터 수집기

KIS API를 통해 차트 데이터를 수집하고 기술지표를 계산합니다.
"""

import logging
import sys
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

sys.path.extend(['..', '.'])
import kis_auth as ka
from dino_test.technical_analyzer import TechnicalData, DinoTestTechnicalAnalyzer

logger = logging.getLogger(__name__)

class TechnicalDataCollector:
    """KIS API를 통한 기술분석 데이터 수집기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = DinoTestTechnicalAnalyzer()
    
    def fetch_chart_data(self, stock_code: str, period: str = "D", adjust: str = "1", count: int = 600) -> Optional[pd.DataFrame]:
        """
        차트 데이터 조회 (2년치 - 반복 호출로 수집)
        
        Args:
            stock_code: 종목코드 (예: '005930')
            period: 기간 구분 (D: 일, W: 주, M: 월)
            adjust: 수정주가 반영 여부 (0: 미반영, 1: 반영)
            count: 조회할 데이터 개수 (최대 600개)
        """
        try:
            from examples_llm.domestic_stock.inquire_daily_itemchartprice.inquire_daily_itemchartprice import inquire_daily_itemchartprice
            from datetime import datetime, timedelta
            import time
            
            all_data = []
            current_end_date = datetime.now()
            target_days = 600  # 2년치 영업일 (약 500-600일)
            
            # 여러 번 호출해서 2년치 데이터 수집
            for batch in range(6):  # 최대 6번 호출 (6 * 100 = 600일)
                # 각 배치별 날짜 범위 계산
                end_date = current_end_date.strftime('%Y%m%d')
                start_date = (current_end_date - timedelta(days=150)).strftime('%Y%m%d')  # 여유있게 150일 범위
                
                self.logger.info(f"배치 {batch+1}: {start_date} ~ {end_date}")
                
                # KIS API 호출
                result1, result2 = inquire_daily_itemchartprice(
                    env_dv="real",  # 실전환경
                    fid_cond_mrkt_div_code="J",  # 주식
                    fid_input_iscd=stock_code,
                    fid_input_date_1=start_date,  # 조회 시작일
                    fid_input_date_2=end_date,    # 조회 종료일
                    fid_period_div_code=period,   # D: 일봉
                    fid_org_adj_prc=adjust        # 1: 원주가
                )
                
                if result2 is not None and not result2.empty:
                    # 표준화 및 추가
                    batch_data = self._standardize_chart_data(result2)
                    if not batch_data.empty:
                        all_data.append(batch_data)
                        self.logger.info(f"배치 {batch+1} 수집 완료: {len(batch_data)} 건")
                    
                    # 다음 배치 준비 (가장 오래된 날짜부터 계속)
                    if not batch_data.empty:
                        oldest_date = batch_data['date'].min()
                        current_end_date = oldest_date - timedelta(days=1)
                    else:
                        break
                else:
                    self.logger.warning(f"배치 {batch+1} 데이터 없음")
                    break
                
                # API 요청 간 간격 (레이트 리밋 대응)
                time.sleep(0.1)
                
                # 충분한 데이터가 모였으면 중단
                total_collected = sum(len(data) for data in all_data)
                if total_collected >= target_days:
                    break
            
            # 모든 배치 데이터 결합
            if all_data:
                combined_data = pd.concat(all_data, ignore_index=True)
                # 날짜별 중복 제거 및 정렬
                combined_data = combined_data.drop_duplicates(subset=['date']).sort_values('date')
                
                self.logger.info(f"차트 데이터 수집 완료 - {stock_code}: {len(combined_data)} 건 "
                               f"({combined_data['date'].min().strftime('%Y-%m-%d')} ~ {combined_data['date'].max().strftime('%Y-%m-%d')})")
                return combined_data
            else:
                self.logger.warning(f"차트 데이터 조회 결과 없음 - {stock_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"차트 데이터 조회 실패 - {stock_code}: {e}")
            return None
    
    def _standardize_chart_data(self, kis_data: pd.DataFrame) -> pd.DataFrame:
        """
        KIS API 차트 데이터를 표준 형식으로 변환
        
        KIS API 컬럼명을 표준 OHLCV 형식으로 매핑:
        - stck_bsop_date → date
        - stck_oprc → open  
        - stck_hgpr → high
        - stck_lwpr → low
        - stck_clpr → close
        - acml_vol → volume
        """
        try:
            # KIS API 컬럼명 매핑 (inquire_daily_itemchartprice API)
            column_mapping = {
                'stck_bsop_date': 'date',  # 주식 영업 일자
                'stck_oprc': 'open',       # 주식 시가
                'stck_hgpr': 'high',       # 주식 최고가
                'stck_lwpr': 'low',        # 주식 최저가
                'stck_clpr': 'close',      # 주식 종가
                'acml_vol': 'volume'       # 누적 거래량
            }
            
            # 필요한 컬럼만 선택하고 이름 변경
            available_columns = [col for col in column_mapping.keys() if col in kis_data.columns]
            
            if not available_columns:
                self.logger.error("KIS API 응답에서 필요한 차트 데이터 컬럼을 찾을 수 없음")
                return pd.DataFrame()
            
            standardized = kis_data[available_columns].copy()
            standardized = standardized.rename(columns=column_mapping)
            
            # 데이터 타입 변환
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in standardized.columns:
                    standardized[col] = pd.to_numeric(standardized[col], errors='coerce')
            
            # 날짜 변환
            if 'date' in standardized.columns:
                standardized['date'] = pd.to_datetime(standardized['date'], format='%Y%m%d', errors='coerce')
            
            # 결측치 제거
            standardized = standardized.dropna()
            
            # 날짜순 정렬 (오래된 날짜부터)
            standardized = standardized.sort_values('date')
            
            self.logger.info(f"차트 데이터 표준화 완료: {len(standardized)} 건")
            return standardized
            
        except Exception as e:
            self.logger.error(f"차트 데이터 표준화 실패: {e}")
            return pd.DataFrame()
    
    def collect_technical_analysis_data(self, stock_code: str) -> Optional[TechnicalData]:
        """
        종목의 기술분석 데이터를 수집하고 지표 계산
        
        Args:
            stock_code: 종목코드 (예: '005930')
            
        Returns:
            TechnicalData 객체 또는 None
        """
        self.logger.info(f"=== {stock_code} 기술분석 데이터 수집 시작 ===")
        
        # 차트 데이터 수집
        chart_data = self.fetch_chart_data(stock_code)
        
        if chart_data is None or chart_data.empty:
            self.logger.error(f"차트 데이터 수집 실패 - {stock_code}")
            return None
        
        # 기술지표 계산
        technical_data = self.analyzer.calculate_chart_data_with_indicators(chart_data)
        
        self.logger.info(f"기술분석 데이터 수집 완료 - {stock_code}")
        
        # 수집된 데이터 로깅 (None 값 처리)
        if technical_data.obv_current is not None:
            obv_2years_text = f"{technical_data.obv_2years_ago:.0f}" if technical_data.obv_2years_ago is not None else "없음"
            self.logger.info(f"OBV: 현재 {technical_data.obv_current:.0f}, 2년전 {obv_2years_text}")
        if technical_data.rsi_current is not None:
            self.logger.info(f"RSI: {technical_data.rsi_current:.2f}")
        if technical_data.price_current is not None:
            price_2years_text = f"{technical_data.price_2years_ago:.0f}원" if technical_data.price_2years_ago is not None else "없음"
            self.logger.info(f"주가: 현재 {technical_data.price_current:.0f}원, 2년전 {price_2years_text}")
        
        return technical_data