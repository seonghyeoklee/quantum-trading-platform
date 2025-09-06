"""
KIS API 전용 데이터 제공자
기존의 복잡한 MultiDataProvider를 대체하는 단순한 KIS API 클라이언트
"""

import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging
import requests
import json

logger = logging.getLogger(__name__)

class KISDataProvider:
    """
    KIS API 전용 데이터 제공자
    
    FastAPI 서버(main.py)를 통해 KIS API에 접근하여 데이터를 가져옵니다.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Args:
            base_url: KIS Adapter FastAPI 서버 주소
        """
        self.base_url = base_url
        self.session = requests.Session()
        
        # 연결 테스트
        self._test_connection()
        
        logger.info(f"KISDataProvider 초기화 완료: {base_url}")
    
    def _test_connection(self):
        """KIS Adapter 서버 연결 테스트"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                logger.info("KIS Adapter 서버 연결 성공")
            else:
                logger.warning(f"KIS Adapter 서버 응답 이상: {response.status_code}")
        except Exception as e:
            logger.error(f"KIS Adapter 서버 연결 실패: {e}")
            logger.warning("서버가 실행 중인지 확인하세요: uv run python main.py")
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """
        현재가 조회
        
        Args:
            symbol: 종목 코드 (예: "005930")
            
        Returns:
            현재가 정보 딕셔너리
        """
        try:
            response = self.session.get(f"{self.base_url}/domestic/price/{symbol}")
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"현재가 조회 성공: {symbol}")
            return data
            
        except Exception as e:
            logger.error(f"현재가 조회 실패 ({symbol}): {e}")
            return {}
    
    def get_chart_data(self, symbol: str, period: str = "D", count: int = 100) -> pd.DataFrame:
        """
        차트 데이터 조회
        
        Args:
            symbol: 종목 코드 (예: "005930")
            period: 기간 (D: 일봉, W: 주봉, M: 월봉, Y: 년봉)
            count: 조회할 데이터 개수
            
        Returns:
            OHLCV 데이터 DataFrame
        """
        try:
            params = {
                "period": period,
                "count": count
            }
            
            response = self.session.get(
                f"{self.base_url}/domestic/chart/{symbol}",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            
            # DataFrame 변환 (실제 KIS API 응답 구조에 맞춤)
            if 'output2' in data and data['output2']:
                df = pd.DataFrame(data['output2'])
                
                # KIS API 컬럼 매핑
                column_mapping = {
                    'stck_bsop_date': 'date',
                    'stck_oprc': 'open',
                    'stck_hgpr': 'high', 
                    'stck_lwpr': 'low',
                    'stck_clpr': 'close',
                    'acml_vol': 'volume'
                }
                
                # 컬럼 이름 변경
                df = df.rename(columns=column_mapping)
                
                # 날짜 컬럼 처리
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                
                # 숫자형 변환
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                logger.debug(f"차트 데이터 조회 성공: {symbol} ({len(df)}행)")
                return df
            else:
                logger.warning(f"차트 데이터 없음: {symbol}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"차트 데이터 조회 실패 ({symbol}): {e}")
            return pd.DataFrame()
    
    def get_index_price(self, index_code: str) -> Dict[str, Any]:
        """
        지수 현재가 조회
        
        Args:
            index_code: 지수 코드 (예: "0001" - 코스피)
            
        Returns:
            지수 정보 딕셔너리
        """
        try:
            response = self.session.get(f"{self.base_url}/domestic/index/{index_code}")
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"지수 조회 성공: {index_code}")
            return data
            
        except Exception as e:
            logger.error(f"지수 조회 실패 ({index_code}): {e}")
            return {}
    
    def get_top_interest_stocks(self, market_type: str = "ALL") -> List[Dict[str, Any]]:
        """
        관심종목 순위 조회
        
        Args:
            market_type: 시장 구분 (ALL, KOSPI, KOSDAQ)
            
        Returns:
            관심종목 리스트
        """
        try:
            params = {"market_type": market_type} if market_type != "ALL" else {}
            
            response = self.session.get(
                f"{self.base_url}/domestic/ranking/top-interest-stock",
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"관심종목 조회 성공: {market_type}")
            return data.get('data', [])
            
        except Exception as e:
            logger.error(f"관심종목 조회 실패 ({market_type}): {e}")
            return []
    
    def get_comprehensive_data(self, symbol: str, days: int = 100) -> Dict[str, Any]:
        """
        종목에 대한 종합 데이터 조회
        
        Args:
            symbol: 종목 코드
            days: 차트 데이터 일수
            
        Returns:
            종합 데이터 딕셔너리
        """
        try:
            # 현재가 정보
            current_price = self.get_current_price(symbol)
            
            # 차트 데이터  
            chart_data = self.get_chart_data(symbol, "D", days)
            
            # 기본 정보 조합
            comprehensive_data = {
                "symbol": symbol,
                "timestamp": datetime.now(),
                "current_price": current_price,
                "chart_data": chart_data,
                "data_source": "KIS_API"
            }
            
            # 기술적 지표 계산 (간단한 이동평균)
            if not chart_data.empty and 'close' in chart_data.columns:
                comprehensive_data['sma_5'] = chart_data['close'].rolling(5).mean().iloc[-1] if len(chart_data) >= 5 else None
                comprehensive_data['sma_20'] = chart_data['close'].rolling(20).mean().iloc[-1] if len(chart_data) >= 20 else None
                comprehensive_data['sma_60'] = chart_data['close'].rolling(60).mean().iloc[-1] if len(chart_data) >= 60 else None
                
                # RSI 계산
                if len(chart_data) >= 14:
                    comprehensive_data['rsi_14'] = self._calculate_rsi(chart_data['close'], 14)
                
                # 거래량 분석
                if 'volume' in chart_data.columns:
                    comprehensive_data['volume_avg_20'] = chart_data['volume'].rolling(20).mean().iloc[-1] if len(chart_data) >= 20 else None
                    
            logger.info(f"종합 데이터 조회 완료: {symbol}")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"종합 데이터 조회 실패 ({symbol}): {e}")
            return {"symbol": symbol, "error": str(e)}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """RSI 계산"""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return rsi.iloc[-1] if not rsi.empty else None
            
        except Exception:
            return None
    
    def get_multiple_symbols_data(self, symbols: List[str], days: int = 100) -> Dict[str, Dict[str, Any]]:
        """
        여러 종목 데이터 동시 조회
        
        Args:
            symbols: 종목 코드 리스트
            days: 차트 데이터 일수
            
        Returns:
            종목별 데이터 딕셔너리
        """
        results = {}
        
        for symbol in symbols:
            try:
                data = self.get_comprehensive_data(symbol, days)
                results[symbol] = data
                
                # Rate limit 고려 (KIS API는 1초당 20건)
                import time
                time.sleep(0.1)  # 100ms 대기
                
            except Exception as e:
                logger.error(f"종목 {symbol} 데이터 조회 실패: {e}")
                results[symbol] = {"symbol": symbol, "error": str(e)}
        
        logger.info(f"다중 종목 데이터 조회 완료: {len(results)}개 종목")
        return results

# 섹터별 종목 정의 (기존 시스템과 호환)
SECTOR_SYMBOLS = {
    "조선": ["009540", "042660"],        # HD한국조선해양, 대우조선해양
    "방산": ["012450", "047810"],        # 한화에어로스페이스, KAI
    "원자력": ["034020", "051600"],      # 두산에너빌리티, 한전KPS
    "AI": ["035420", "035720"],          # NAVER, 카카오
    "반도체": ["005930", "000660"],      # 삼성전자, SK하이닉스
    "바이오": ["207940", "068270"]       # 삼성바이오로직스, 셀트리온
}

def get_all_sector_symbols() -> List[str]:
    """모든 섹터의 종목 코드 리스트 반환"""
    all_symbols = []
    for symbols in SECTOR_SYMBOLS.values():
        all_symbols.extend(symbols)
    return all_symbols