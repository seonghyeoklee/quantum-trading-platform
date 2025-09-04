"""
다중 데이터 소스 통합 공급자
PyKRX, FinanceDataReader, yfinance, KIS API를 통합하여 최적의 데이터 제공
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import warnings

# 경고 메시지 무시
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class DataSource(Enum):
    """데이터 소스 타입"""
    KIS_API = "KIS_API"
    PYKRX = "PYKRX" 
    FINANCE_DATAREADER = "FINANCE_DATAREADER"
    YFINANCE = "YFINANCE"
    AUTO = "AUTO"  # 자동 선택

class DataQuality(Enum):
    """데이터 품질 등급"""
    EXCELLENT = "EXCELLENT"  # 완전한 데이터
    GOOD = "GOOD"           # 약간의 결측치
    FAIR = "FAIR"           # 상당한 결측치
    POOR = "POOR"           # 심각한 데이터 문제

@dataclass
class DataSourceInfo:
    """데이터 소스 정보"""
    source: DataSource
    success: bool
    data_points: int
    response_time: float
    quality: DataQuality
    error_message: str = ""

@dataclass
class MarketData:
    """시장 데이터 표준 형식"""
    symbol: str
    data: pd.DataFrame  # OHLCV + 추가 컬럼
    source: DataSource
    quality: DataQuality
    timestamp: datetime
    metadata: Dict = None

class MultiDataProvider:
    """
    다중 데이터 소스 통합 공급자
    
    우선순위:
    1. KIS API (실시간, 정확)
    2. PyKRX (KRX 직접, 빠름)  
    3. FinanceDataReader (다양한 소스)
    4. yfinance (글로벌, 안정성)
    """
    
    def __init__(self, enable_kis: bool = True, cache_enabled: bool = True):
        """
        Args:
            enable_kis: KIS API 사용 여부
            cache_enabled: 데이터 캐싱 사용 여부
        """
        self.enable_kis = enable_kis
        self.cache_enabled = cache_enabled
        self.cache = {} if cache_enabled else None
        
        # 데이터 소스별 성능 통계
        self.performance_stats = {
            source: {"calls": 0, "success": 0, "avg_time": 0.0, "failures": []}
            for source in DataSource if source != DataSource.AUTO
        }
        
        # 소스별 가용성 확인
        self.available_sources = self._check_available_sources()
        
        logger.info(f"MultiDataProvider 초기화 완료")
        logger.info(f"사용 가능한 소스: {[s.value for s in self.available_sources]}")
    
    def _check_available_sources(self) -> List[DataSource]:
        """사용 가능한 데이터 소스 확인"""
        available = []
        
        # PyKRX 확인
        try:
            import pykrx
            available.append(DataSource.PYKRX)
        except ImportError:
            logger.warning("PyKRX 사용 불가")
        
        # FinanceDataReader 확인
        try:
            import FinanceDataReader
            available.append(DataSource.FINANCE_DATAREADER)
        except ImportError:
            logger.warning("FinanceDataReader 사용 불가")
        
        # yfinance 확인
        try:
            import yfinance
            available.append(DataSource.YFINANCE)
        except ImportError:
            logger.warning("yfinance 사용 불가")
        
        # KIS API 확인 (선택적)
        if self.enable_kis:
            available.append(DataSource.KIS_API)
        
        return available
    
    def get_stock_data(self, 
                      symbol: str, 
                      start_date: Union[str, datetime], 
                      end_date: Union[str, datetime] = None,
                      source: DataSource = DataSource.AUTO,
                      fallback: bool = True) -> Optional[MarketData]:
        """
        주식 데이터 조회 (통합 인터페이스)
        
        Args:
            symbol: 종목 코드
            start_date: 시작일
            end_date: 종료일 (None이면 오늘)
            source: 데이터 소스 (AUTO면 자동 선택)
            fallback: 실패 시 다른 소스 시도 여부
            
        Returns:
            MarketData 객체 또는 None
        """
        # 날짜 정규화
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date is None:
            end_date = datetime.now()
        elif isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        # 캐시 확인
        cache_key = f"{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        if self.cache_enabled and cache_key in self.cache:
            logger.debug(f"캐시에서 데이터 반환: {symbol}")
            return self.cache[cache_key]
        
        # 데이터 소스 선택
        if source == DataSource.AUTO:
            sources_to_try = self._get_optimal_sources(symbol, start_date, end_date)
        else:
            sources_to_try = [source] if source in self.available_sources else []
            if fallback:
                # 실패 시 시도할 다른 소스들 추가
                sources_to_try.extend([s for s in self.available_sources if s != source])
        
        # 각 소스 시도
        for data_source in sources_to_try:
            try:
                result = self._fetch_from_source(data_source, symbol, start_date, end_date)
                if result:
                    # 성공 시 캐시 저장
                    if self.cache_enabled:
                        self.cache[cache_key] = result
                    
                    # 성능 통계 업데이트
                    self._update_performance_stats(data_source, True, result.metadata.get('response_time', 0))
                    
                    logger.info(f"✅ {data_source.value}에서 데이터 조회 성공: {symbol} ({len(result.data)}일)")
                    return result
                    
            except Exception as e:
                logger.warning(f"❌ {data_source.value} 데이터 조회 실패: {symbol} - {e}")
                self._update_performance_stats(data_source, False, 0, str(e))
                continue
        
        logger.error(f"❌ 모든 소스에서 데이터 조회 실패: {symbol}")
        return None
    
    def _get_optimal_sources(self, symbol: str, start_date: datetime, end_date: datetime) -> List[DataSource]:
        """최적의 데이터 소스 순서 결정"""
        # 기본 우선순위
        priority_order = [
            DataSource.PYKRX,           # 가장 빠름
            DataSource.FINANCE_DATAREADER,  # 안정적
            DataSource.YFINANCE,        # 글로벌
            DataSource.KIS_API          # 실시간 (있을 경우)
        ]
        
        # 성능 통계 기반 재정렬
        available_with_stats = []
        for source in priority_order:
            if source in self.available_sources:
                stats = self.performance_stats[source]
                success_rate = stats["success"] / max(stats["calls"], 1)
                avg_time = stats["avg_time"]
                
                # 점수 계산 (성공률 70%, 속도 30%)
                score = success_rate * 0.7 + (1 / (avg_time + 0.1)) * 0.3
                available_with_stats.append((source, score))
        
        # 점수순으로 정렬
        available_with_stats.sort(key=lambda x: x[1], reverse=True)
        
        return [source for source, _ in available_with_stats]
    
    def _fetch_from_source(self, source: DataSource, symbol: str, 
                          start_date: datetime, end_date: datetime) -> Optional[MarketData]:
        """특정 소스에서 데이터 조회"""
        start_time = time.time()
        
        try:
            if source == DataSource.PYKRX:
                return self._fetch_pykrx(symbol, start_date, end_date, start_time)
            elif source == DataSource.FINANCE_DATAREADER:
                return self._fetch_fdr(symbol, start_date, end_date, start_time)
            elif source == DataSource.YFINANCE:
                return self._fetch_yfinance(symbol, start_date, end_date, start_time)
            elif source == DataSource.KIS_API:
                return self._fetch_kis_api(symbol, start_date, end_date, start_time)
            
        except Exception as e:
            logger.error(f"데이터 조회 오류 ({source.value}): {e}")
            return None
    
    def _fetch_pykrx(self, symbol: str, start_date: datetime, end_date: datetime, start_time: float) -> Optional[MarketData]:
        """PyKRX에서 데이터 조회"""
        from pykrx import stock
        
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        df = stock.get_market_ohlcv_by_date(start_str, end_str, symbol)
        
        if df.empty:
            return None
        
        # 컬럼명 표준화
        df = df.rename(columns={
            '시가': 'open', '고가': 'high', '저가': 'low', 
            '종가': 'close', '거래량': 'volume'
        })
        
        # 데이터 품질 평가
        quality = self._evaluate_data_quality(df)
        
        response_time = time.time() - start_time
        
        return MarketData(
            symbol=symbol,
            data=df,
            source=DataSource.PYKRX,
            quality=quality,
            timestamp=datetime.now(),
            metadata={'response_time': response_time, 'source_info': 'KRX 직접 스크래핑'}
        )
    
    def _fetch_fdr(self, symbol: str, start_date: datetime, end_date: datetime, start_time: float) -> Optional[MarketData]:
        """FinanceDataReader에서 데이터 조회"""
        import FinanceDataReader as fdr
        
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        df = fdr.DataReader(symbol, start_str, end_str)
        
        if df.empty:
            return None
        
        # 컬럼명 표준화 (소문자 변환)
        df.columns = df.columns.str.lower()
        if 'change' in df.columns:
            df = df.drop(columns=['change'])  # 변화율 제거
        
        quality = self._evaluate_data_quality(df)
        response_time = time.time() - start_time
        
        return MarketData(
            symbol=symbol,
            data=df,
            source=DataSource.FINANCE_DATAREADER,
            quality=quality,
            timestamp=datetime.now(),
            metadata={'response_time': response_time, 'source_info': 'FinanceDataReader 멀티소스'}
        )
    
    def _fetch_yfinance(self, symbol: str, start_date: datetime, end_date: datetime, start_time: float) -> Optional[MarketData]:
        """yfinance에서 데이터 조회"""
        import yfinance as yf
        
        # 한국 주식은 .KS 접미사 추가
        if len(symbol) == 6 and symbol.isdigit():
            yf_symbol = f"{symbol}.KS"
        else:
            yf_symbol = symbol
        
        ticker = yf.Ticker(yf_symbol)
        
        # 기간 계산
        days = (end_date - start_date).days
        if days <= 7:
            period = "1wk"
        elif days <= 30:
            period = "1mo"
        elif days <= 90:
            period = "3mo"
        else:
            period = "1y"
        
        df = ticker.history(period=period, start=start_date, end=end_date)
        
        if df.empty:
            return None
        
        # 시간대 정보 제거
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
            
        # 컬럼명 소문자 변환
        df.columns = df.columns.str.lower()
        
        quality = self._evaluate_data_quality(df)
        response_time = time.time() - start_time
        
        return MarketData(
            symbol=symbol,
            data=df,
            source=DataSource.YFINANCE,
            quality=quality,
            timestamp=datetime.now(),
            metadata={'response_time': response_time, 'source_info': f'Yahoo Finance ({yf_symbol})'}
        )
    
    def _fetch_kis_api(self, symbol: str, start_date: datetime, end_date: datetime, start_time: float) -> Optional[MarketData]:
        """KIS API에서 데이터 조회 (향후 구현)"""
        # TODO: 기존 KIS API 연동
        logger.info("KIS API 연동 예정")
        return None
    
    def _evaluate_data_quality(self, df: pd.DataFrame) -> DataQuality:
        """데이터 품질 평가"""
        if df.empty:
            return DataQuality.POOR
        
        # 필수 컬럼 확인
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return DataQuality.POOR
        
        # 결측치 비율 계산
        missing_ratio = df[required_cols].isnull().sum().sum() / (len(df) * len(required_cols))
        
        # 데이터 일관성 확인
        inconsistent = 0
        for col in ['Open', 'High', 'Low', 'Close']:
            if (df[col] <= 0).any():
                inconsistent += 1
        
        # High >= Low 확인
        if (df['High'] < df['Low']).any():
            inconsistent += 1
        
        # 품질 등급 결정
        if missing_ratio == 0 and inconsistent == 0:
            return DataQuality.EXCELLENT
        elif missing_ratio < 0.05 and inconsistent <= 1:
            return DataQuality.GOOD
        elif missing_ratio < 0.15 and inconsistent <= 2:
            return DataQuality.FAIR
        else:
            return DataQuality.POOR
    
    def _update_performance_stats(self, source: DataSource, success: bool, response_time: float, error_msg: str = ""):
        """성능 통계 업데이트"""
        stats = self.performance_stats[source]
        stats["calls"] += 1
        
        if success:
            stats["success"] += 1
            # 평균 응답 시간 업데이트
            total_time = stats["avg_time"] * (stats["calls"] - 1) + response_time
            stats["avg_time"] = total_time / stats["calls"]
        else:
            stats["failures"].append({
                "timestamp": datetime.now().isoformat(),
                "error": error_msg
            })
            # 최근 10개만 유지
            if len(stats["failures"]) > 10:
                stats["failures"] = stats["failures"][-10:]
    
    def get_performance_report(self) -> Dict:
        """성능 리포트 생성"""
        report = {}
        
        for source, stats in self.performance_stats.items():
            if stats["calls"] > 0:
                success_rate = stats["success"] / stats["calls"] * 100
                report[source.value] = {
                    "총_호출수": stats["calls"],
                    "성공_횟수": stats["success"],
                    "성공률": f"{success_rate:.1f}%",
                    "평균_응답시간": f"{stats['avg_time']:.3f}초",
                    "최근_실패": len(stats["failures"])
                }
        
        return report
    
    def clear_cache(self):
        """캐시 초기화"""
        if self.cache_enabled:
            self.cache.clear()
            logger.info("데이터 캐시 초기화 완료")
    
    def get_cache_info(self) -> Dict:
        """캐시 정보 반환"""
        if not self.cache_enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "entries": len(self.cache),
            "keys": list(self.cache.keys())
        }