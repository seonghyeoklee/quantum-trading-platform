"""
디노테스트 재무 데이터 수집기

KIS API를 통해 재무 데이터를 수집하고 DinoTestFinanceScorer에서 사용할 수 있는 형태로 변환합니다.
"""

import logging
import sys
import pandas as pd
from typing import Optional, Dict, Any
from decimal import Decimal
from dataclasses import asdict

sys.path.extend(['..', '.'])
import kis_auth as ka
from dino_test.finance_scorer import FinanceData

logger = logging.getLogger(__name__)

class FinanceDataCollector:
    """KIS API를 통한 재무 데이터 수집기"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def fetch_income_statement(self, stock_code: str, div_cls_code: str = "0") -> Optional[pd.DataFrame]:
        """
        손익계산서 데이터 조회
        
        Args:
            stock_code: 종목코드 (예: '005930')
            div_cls_code: 분류구분코드 (0: 년, 1: 분기)
        """
        try:
            from examples_llm.domestic_stock.finance_income_statement.finance_income_statement import finance_income_statement
            
            result = finance_income_statement(
                fid_div_cls_code=div_cls_code,
                fid_cond_mrkt_div_code="J", 
                fid_input_iscd=stock_code
            )
            
            if result is not None and not result.empty:
                self.logger.info(f"손익계산서 조회 성공 - {stock_code}: {len(result)} 건")
                return result
            else:
                self.logger.warning(f"손익계산서 조회 결과 없음 - {stock_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"손익계산서 조회 실패 - {stock_code}: {e}")
            return None
    
    def fetch_balance_sheet(self, stock_code: str, div_cls_code: str = "0") -> Optional[pd.DataFrame]:
        """
        대차대조표 데이터 조회
        
        Args:
            stock_code: 종목코드 (예: '005930')
            div_cls_code: 분류구분코드 (0: 년, 1: 분기)
        """
        try:
            from examples_llm.domestic_stock.finance_balance_sheet.finance_balance_sheet import finance_balance_sheet
            
            result = finance_balance_sheet(
                fid_div_cls_code=div_cls_code,
                fid_cond_mrkt_div_code="J",
                fid_input_iscd=stock_code
            )
            
            if result is not None and not result.empty:
                self.logger.info(f"대차대조표 조회 성공 - {stock_code}: {len(result)} 건")
                return result
            else:
                self.logger.warning(f"대차대조표 조회 결과 없음 - {stock_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"대차대조표 조회 실패 - {stock_code}: {e}")
            return None
    
    def fetch_financial_ratio(self, stock_code: str, div_cls_code: str = "0") -> Optional[pd.DataFrame]:
        """
        재무비율 데이터 조회
        
        Args:
            stock_code: 종목코드 (예: '005930')
            div_cls_code: 분류구분코드 (0: 년, 1: 분기)
        """
        try:
            from examples_llm.domestic_stock.finance_financial_ratio.finance_financial_ratio import finance_financial_ratio
            
            result = finance_financial_ratio(
                fid_div_cls_code=div_cls_code,
                fid_cond_mrkt_div_code="J",
                fid_input_iscd=stock_code
            )
            
            if result is not None and not result.empty:
                self.logger.info(f"재무비율 조회 성공 - {stock_code}: {len(result)} 건")
                return result
            else:
                self.logger.warning(f"재무비율 조회 결과 없음 - {stock_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"재무비율 조회 실패 - {stock_code}: {e}")
            return None
    
    def fetch_stability_ratio(self, stock_code: str, div_cls_code: str = "0") -> Optional[pd.DataFrame]:
        """
        안정성비율 데이터 조회
        
        Args:
            stock_code: 종목코드 (예: '005930')
            div_cls_code: 분류구분코드 (0: 년, 1: 분기)
        """
        try:
            from examples_llm.domestic_stock.finance_stability_ratio.finance_stability_ratio import finance_stability_ratio
            
            result = finance_stability_ratio(
                fid_input_iscd=stock_code,
                fid_div_cls_code=div_cls_code,
                fid_cond_mrkt_div_code="J"
            )
            
            if result is not None and not result.empty:
                self.logger.info(f"안정성비율 조회 성공 - {stock_code}: {len(result)} 건")
                return result
            else:
                self.logger.warning(f"안정성비율 조회 결과 없음 - {stock_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"안정성비율 조회 실패 - {stock_code}: {e}")
            return None
    
    def parse_finance_data(self, stock_code: str) -> Optional[FinanceData]:
        """
        종목의 재무 데이터를 수집하고 FinanceData 객체로 변환
        
        Args:
            stock_code: 종목코드 (예: '005930')
            
        Returns:
            FinanceData 객체 또는 None
        """
        self.logger.info(f"=== {stock_code} 재무 데이터 수집 시작 ===")
        
        # 연간 데이터 수집 (최근 2년)
        income_statement = self.fetch_income_statement(stock_code, "0")  # 연간 
        balance_sheet = self.fetch_balance_sheet(stock_code, "0")        # 연간
        financial_ratio = self.fetch_financial_ratio(stock_code, "0")    # 연간
        stability_ratio = self.fetch_stability_ratio(stock_code, "0")    # 연간
        
        if not any([income_statement is not None, balance_sheet is not None]):
            self.logger.error(f"필수 재무 데이터 조회 실패 - {stock_code}")
            return None
        
        finance_data = FinanceData()
        current_period = None
        previous_period = None
        
        try:
            # 손익계산서 데이터 파싱
            if income_statement is not None and len(income_statement) >= 2:
                # 최신 2년 데이터 가정 (실제 API 응답 구조에 따라 조정 필요)
                current_year = income_statement.iloc[0]
                previous_year = income_statement.iloc[1]
                
                # 기준 연월 수집 (YYYYMM 형식)
                if 'stac_yymm' in current_year:
                    current_period = str(current_year['stac_yymm'])
                if 'stac_yymm' in previous_year:
                    previous_period = str(previous_year['stac_yymm'])
                
                # 실제 KIS API 컬럼명으로 매출액 파싱
                revenue_columns = ['sale_account', '매출액', 'revenue', 'sales', 'total_revenue']
                operating_profit_columns = ['op_prfi', '영업이익', 'operating_profit', 'operating_income']
                
                for col in revenue_columns:
                    if col in current_year:
                        finance_data.current_revenue = self._safe_decimal(current_year[col])
                        break
                
                for col in revenue_columns:
                    if col in previous_year:
                        finance_data.previous_revenue = self._safe_decimal(previous_year[col])
                        break
                
                for col in operating_profit_columns:
                    if col in current_year:
                        finance_data.current_operating_profit = self._safe_decimal(current_year[col])
                        break
                
                for col in operating_profit_columns:
                    if col in previous_year:
                        finance_data.previous_operating_profit = self._safe_decimal(previous_year[col])
                        break
            
            # 대차대조표 데이터 파싱
            if balance_sheet is not None and not balance_sheet.empty:
                current_bs = balance_sheet.iloc[0]
                
                debt_columns = ['total_lblt', '총부채', 'total_debt', 'total_liabilities']
                equity_columns = ['total_cptl', '자기자본', 'total_equity', 'shareholders_equity']
                retained_earnings_columns = ['rsrv', '이익잉여금', 'retained_earnings']
                capital_stock_columns = ['cpfn', '자본금', 'capital_stock', 'paid_in_capital']
                
                for col in debt_columns:
                    if col in current_bs:
                        finance_data.total_debt = self._safe_decimal(current_bs[col])
                        break
                
                for col in equity_columns:
                    if col in current_bs:
                        finance_data.total_equity = self._safe_decimal(current_bs[col])
                        break
                
                for col in retained_earnings_columns:
                    if col in current_bs:
                        finance_data.retained_earnings = self._safe_decimal(current_bs[col])
                        break
                
                for col in capital_stock_columns:
                    if col in current_bs:
                        finance_data.capital_stock = self._safe_decimal(current_bs[col])
                        break
            
            # 재무비율 데이터 파싱 (영업이익률, 유보율)
            if financial_ratio is not None and not financial_ratio.empty:
                current_ratio = financial_ratio.iloc[0]
                
                margin_columns = ['bsop_prfi_inrt', '영업이익률', 'operating_margin', 'operating_profit_margin']
                for col in margin_columns:
                    if col in current_ratio:
                        finance_data.operating_margin = self._safe_decimal(current_ratio[col])
                        break
                
                # 유보율은 KIS API에서 이미 계산된 값으로 제공 (rsrv_rate)
                retention_rate_columns = ['rsrv_rate', '유보율', 'retention_rate']
                for col in retention_rate_columns:
                    if col in current_ratio:
                        retention_rate_value = self._safe_decimal(current_ratio[col])
                        if retention_rate_value is not None:
                            # rsrv_rate는 이미 %값이므로 직접 사용
                            finance_data.retention_rate = retention_rate_value
                        break
            
            # 기준 연월 설정
            finance_data.current_period = current_period
            finance_data.previous_period = previous_period
            
            self.logger.info(f"재무 데이터 파싱 완료 - {stock_code}")
            self.logger.debug(f"파싱된 데이터: {asdict(finance_data)}")
            
            return finance_data
            
        except Exception as e:
            self.logger.error(f"재무 데이터 파싱 실패 - {stock_code}: {e}")
            return None
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """
        안전한 Decimal 변환
        
        Args:
            value: 변환할 값
            
        Returns:
            Decimal 값 또는 None
        """
        if value is None or pd.isna(value):
            return None
        
        try:
            if isinstance(value, str):
                # 쉼표 제거 및 숫자가 아닌 문자 처리
                cleaned = str(value).replace(',', '').replace(' ', '')
                if cleaned == '' or cleaned == '-':
                    return None
                return Decimal(cleaned)
            else:
                return Decimal(str(value))
        except (ValueError, TypeError, Exception):
            self.logger.debug(f"Decimal 변환 실패: {value}")
            return None