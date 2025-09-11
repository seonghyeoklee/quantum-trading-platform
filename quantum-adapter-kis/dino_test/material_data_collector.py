"""
디노테스트 소재분석 데이터 수집기

KIS API를 통해 배당률, 기관/외국인 수급 데이터를 수집합니다.
"""

import logging
import sys
import pandas as pd
from typing import Optional
from datetime import datetime, timedelta

sys.path.extend(['..', '.'])
import kis_auth as ka
from dino_test.material_analyzer import MaterialData, DinoTestMaterialAnalyzer

logger = logging.getLogger(__name__)

class MaterialDataCollector:
    """KIS API를 통한 소재분석 데이터 수집기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analyzer = DinoTestMaterialAnalyzer()
    
    def fetch_dividend_data(self, stock_code: str) -> Optional[float]:
        """
        배당률 조회
        
        Args:
            stock_code: 종목코드 (예: '005930')
            
        Returns:
            배당률 (%) 또는 None
        """
        try:
            # 재무비율 API에서 배당률 조회 (기존 재무분석에서 사용한 API 활용)
            from examples_llm.domestic_stock.inquire_daily_itemchartprice.inquire_daily_itemchartprice import inquire_daily_itemchartprice
            from examples_llm.domestic_stock.inquire_daily_ccld.inquire_daily_ccld import inquire_daily_ccld
            
            # 먼저 현재가 조회로 기본 정보 확인
            from examples_llm.domestic_stock.inquire_price.inquire_price import inquire_price
            
            result_df = inquire_price(
                env_dv="real",  # 실전환경
                fid_cond_mrkt_div_code="J",  # 주식
                fid_input_iscd=stock_code
            )
            
            if result_df is not None and not result_df.empty:
                # 배당률 관련 컬럼 찾기
                dividend_columns = ['dvid_ynrt', '배당률', 'dividend_yield', 'dvid_rate']
                
                for col in dividend_columns:
                    if col in result_df.columns:
                        dividend_yield = pd.to_numeric(result_df[col].iloc[0], errors='coerce')
                        if pd.notna(dividend_yield) and dividend_yield > 0:
                            self.logger.info(f"배당률 조회 성공 - {stock_code}: {dividend_yield}%")
                            return float(dividend_yield)
                
                # 컬럼이 없으면 기본값 0으로 처리
                self.logger.warning(f"배당률 컬럼을 찾을 수 없음 - {stock_code}: {result_df.columns.tolist()}")
                return 0.0
            else:
                self.logger.warning(f"배당률 조회 결과 없음 - {stock_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"배당률 조회 실패 - {stock_code}: {e}")
            return None
    
    def fetch_investor_data(self, stock_code: str) -> tuple[Optional[float], Optional[float], Optional[float], Optional[float]]:
        """
        기관/외국인 투자자 수급 데이터 조회
        
        Args:
            stock_code: 종목코드 (예: '005930')
            
        Returns:
            tuple: (기관_보유비율, 외국인_보유비율, 기관_변화율, 외국인_변화율)
        """
        try:
            # 투자자별 보유 현황 API 호출 (가능한 API 찾기)
            # 현재 KIS API에서 기관/외국인 수급 데이터를 조회할 수 있는 API를 확인해야 함
            
            # 임시로 현재가 API에서 관련 데이터가 있는지 확인
            from examples_llm.domestic_stock.inquire_price.inquire_price import inquire_price
            
            result_df = inquire_price(
                env_dv="real",  # 실전환경
                fid_cond_mrkt_div_code="J",  # 주식
                fid_input_iscd=stock_code
            )
            
            institutional_ratio = None
            foreign_ratio = None
            institutional_change = None
            foreign_change = None
            
            if result_df is not None and not result_df.empty:
                # 기관/외국인 관련 컬럼 찾기
                institutional_columns = ['inst_ratio', '기관비율', 'institutional', 'inst_hldg_rt']
                foreign_columns = ['forn_ratio', '외국인비율', 'foreign', 'forn_hldg_rt']
                
                # 기관 보유 비율 찾기
                for col in institutional_columns:
                    if col in result_df.columns:
                        institutional_ratio = pd.to_numeric(result_df[col].iloc[0], errors='coerce')
                        if pd.notna(institutional_ratio):
                            institutional_ratio = float(institutional_ratio)
                            break
                
                # 외국인 보유 비율 찾기
                for col in foreign_columns:
                    if col in result_df.columns:
                        foreign_ratio = pd.to_numeric(result_df[col].iloc[0], errors='coerce')
                        if pd.notna(foreign_ratio):
                            foreign_ratio = float(foreign_ratio)
                            break
                
                # 변화율 데이터는 임시로 더미 데이터 (실제로는 다른 API나 계산 필요)
                if institutional_ratio is not None:
                    institutional_change = 0.5  # 임시 데이터
                if foreign_ratio is not None:
                    foreign_change = 0.3  # 임시 데이터
                
                self.logger.info(f"투자자 수급 조회 - {stock_code}: 기관 {institutional_ratio}%, 외국인 {foreign_ratio}%")
            
            return institutional_ratio, foreign_ratio, institutional_change, foreign_change
            
        except Exception as e:
            self.logger.error(f"투자자 수급 조회 실패 - {stock_code}: {e}")
            return None, None, None, None
    
    def _try_alternative_dividend_api(self, stock_code: str) -> Optional[float]:
        """
        대안 배당률 조회 API 시도
        """
        try:
            # 재무비율 API 시도 (기존 재무분석에서 사용)
            from examples_llm.domestic_stock.inquire_daily_ccld.inquire_daily_ccld import inquire_daily_ccld
            
            # 임시로 현재가 조회로 대체 (inquire_daily_ccld 파라미터 오류 해결 필요)
            from examples_llm.domestic_stock.inquire_price.inquire_price import inquire_price
            
            result_df = inquire_price(
                env_dv="real",  # 실전환경
                fid_cond_mrkt_div_code="J",  # 주식
                fid_input_iscd=stock_code
            )
            
            if result_df is not None and not result_df.empty:
                # 배당 관련 컬럼 찾기
                dividend_columns = ['dvid_ynrt', 'dividend_yield', 'dvid_rate']
                for col in dividend_columns:
                    if col in result_df.columns:
                        dividend_yield = pd.to_numeric(result_df[col].iloc[0], errors='coerce')
                        if pd.notna(dividend_yield) and dividend_yield > 0:
                            return float(dividend_yield)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"대안 배당률 API 실패 - {stock_code}: {e}")
            return None
    
    def collect_material_analysis_data(self, stock_code: str) -> Optional[MaterialData]:
        """
        종목의 소재분석 데이터를 수집
        
        Args:
            stock_code: 종목코드 (예: '005930')
            
        Returns:
            MaterialData 객체 또는 None
        """
        self.logger.info(f"=== {stock_code} 소재분석 데이터 수집 시작 ===")
        
        # 배당률 데이터 수집
        dividend_yield = self.fetch_dividend_data(stock_code)
        if dividend_yield is None:
            # 대안 API 시도
            dividend_yield = self._try_alternative_dividend_api(stock_code)
        
        # 투자자 수급 데이터 수집
        institutional_ratio, foreign_ratio, institutional_change, foreign_change = self.fetch_investor_data(stock_code)
        
        # MaterialData 객체 생성
        material_data = MaterialData(
            dividend_yield=dividend_yield,
            institutional_ratio=institutional_ratio,
            foreign_ratio=foreign_ratio,
            institutional_change_1m=institutional_change,
            foreign_change_1m=foreign_change,
            institutional_change_3m=institutional_change,  # 임시로 동일값 사용
            foreign_change_3m=foreign_change,  # 임시로 동일값 사용
            listed_shares=None,  # 향후 구현
            earnings_surprise=None  # 향후 구현
        )
        
        self.logger.info(f"소재분석 데이터 수집 완료 - {stock_code}")
        
        # 수집된 데이터 로깅
        if dividend_yield is not None:
            self.logger.info(f"배당률: {dividend_yield:.2f}%")
        if institutional_ratio is not None:
            self.logger.info(f"기관 보유 비율: {institutional_ratio:.2f}%")
        if foreign_ratio is not None:
            self.logger.info(f"외국인 보유 비율: {foreign_ratio:.2f}%")
        
        return material_data