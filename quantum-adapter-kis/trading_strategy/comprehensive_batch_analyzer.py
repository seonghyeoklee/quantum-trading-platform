#!/usr/bin/env python3
"""
종합 주식 분석 배치 시스템
국내/해외, 다양한 섹터 종목을 체계적으로 분석하여 JSON과 PostgreSQL에 저장

Author: Quantum Trading Platform
Created: 2025-02-04
"""

import asyncio
import json
import time
import logging
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

# 현재 폴더 경로 추가
import sys
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))
sys.path.append(str(current_dir.parent))

# 분석 엔진 import
try:
    from core.kis_data_provider import KISDataProvider, SECTOR_SYMBOLS, get_all_sector_symbols
    from core.signal_detector import SignalDetector
    from core.technical_analysis import TechnicalAnalyzer
    from core.backtester import GoldenCrossBacktester
except ImportError as e:
    print(f"⚠️  분석 엔진 import 실패: {e}")
    print("core 모듈이 있는지 확인해주세요.")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class ComprehensiveBatchAnalyzer:
    """종합 주식 분석 배치 시스템"""
    
    def __init__(self):
        """초기화"""
        logger.info("🚀 종합 분석 시스템 초기화 중...")
        
        # 분석 엔진 초기화 (KIS API 중심화)
        self.provider = KISDataProvider(base_url="http://localhost:8000")
        self.signal_detector = SignalDetector()
        self.technical_analyzer = TechnicalAnalyzer()
        self.backtester = GoldenCrossBacktester()
        
        # PostgreSQL 연결 (나중에 활성화)
        self.db_conn = None
        
        # 전체 종목 마스터 데이터 (KIS API 기반 섹터 시스템과 동기화)
        self.symbol_registry = self._load_symbols_from_sectors()
        
        logger.info(f"✅ 초기화 완료 - 총 {len(self.symbol_registry)}개 종목 로드")
    
    def _load_symbols_from_sectors(self) -> Dict[str, Dict]:
        """KIS API 기반 섹터 시스템과 동기화된 종목 마스터 데이터 로드"""
        
        # 종목명 매핑 (KIS API에서 가져올 수 있지만 일단 하드코딩)
        stock_names = {
            "009540": "HD한국조선해양",
            "042660": "대우조선해양", 
            "012450": "한화에어로스페이스",
            "047810": "KAI",
            "034020": "두산에너빌리티", 
            "051600": "한전KPS",
            "035420": "NAVER",
            "035720": "카카오",
            "005930": "삼성전자",
            "000660": "SK하이닉스",
            "207940": "삼성바이오로직스",
            "068270": "셀트리온"
        }
        
        symbol_registry = {}
        
        # SECTOR_SYMBOLS에서 종목 정보 생성
        for sector_name, symbols in SECTOR_SYMBOLS.items():
            for symbol in symbols:
                symbol_registry[symbol] = {
                    "name": stock_names.get(symbol, f"종목_{symbol}"),
                    "name_en": stock_names.get(symbol, f"Stock_{symbol}"),
                    "market_type": "DOMESTIC",
                    "exchange": "KRX", 
                    "country": "KR",
                    "sector_l1": sector_name,
                    "sector_l2": sector_name,
                    "sector_l3": sector_name,
                    "market_cap_tier": "LARGE"
                }
        
        logger.info(f"섹터 기반 심볼 레지스트리 로드 완료: {len(symbol_registry)}개 종목")
        return symbol_registry

    def _load_symbols_old(self) -> Dict[str, Dict]:
        """종목 마스터 데이터 로드"""
        return {
            # ============= 국내 주요 종목 =============
            
            # 반도체 섹터
            "005930": {
                "name": "삼성전자", "name_en": "Samsung Electronics",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "IT", "sector_l2": "반도체", "sector_l3": "종합반도체",
                "market_cap_tier": "LARGE"
            },
            "000660": {
                "name": "SK하이닉스", "name_en": "SK Hynix", 
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "IT", "sector_l2": "반도체", "sector_l3": "메모리반도체",
                "market_cap_tier": "LARGE"
            },
            "042700": {
                "name": "한미반도체", "name_en": "Hanmi Semiconductor",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR", 
                "sector_l1": "IT", "sector_l2": "반도체", "sector_l3": "반도체장비",
                "market_cap_tier": "MID"
            },
            
            # IT/인터넷 서비스
            "035720": {
                "name": "카카오", "name_en": "Kakao",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "IT", "sector_l2": "인터넷서비스", "sector_l3": "플랫폼",
                "market_cap_tier": "LARGE"
            },
            "035420": {
                "name": "NAVER", "name_en": "NAVER",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "IT", "sector_l2": "인터넷서비스", "sector_l3": "포털",
                "market_cap_tier": "LARGE"
            },
            "036570": {
                "name": "엔씨소프트", "name_en": "NCsoft",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "IT", "sector_l2": "게임", "sector_l3": "온라인게임",
                "market_cap_tier": "LARGE"
            },
            
            # 바이오/제약
            "207940": {
                "name": "삼성바이오로직스", "name_en": "Samsung Biologics",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "바이오", "sector_l2": "바이오의약품", "sector_l3": "CDMO",
                "market_cap_tier": "LARGE"
            },
            "068270": {
                "name": "셀트리온", "name_en": "Celltrion",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "바이오", "sector_l2": "바이오의약품", "sector_l3": "항체의약품",
                "market_cap_tier": "LARGE"
            },
            "326030": {
                "name": "SK바이오팜", "name_en": "SK Biopharmaceuticals",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "바이오", "sector_l2": "바이오의약품", "sector_l3": "신경계질환",
                "market_cap_tier": "LARGE"
            },
            
            # 2차전지
            "373220": {
                "name": "LG에너지솔루션", "name_en": "LG Energy Solution",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "전기전자", "sector_l2": "2차전지", "sector_l3": "리튬이온전지",
                "market_cap_tier": "LARGE"
            },
            "051910": {
                "name": "LG화학", "name_en": "LG Chem",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "화학", "sector_l2": "종합화학", "sector_l3": "석유화학",
                "market_cap_tier": "LARGE"
            },
            "006400": {
                "name": "삼성SDI", "name_en": "Samsung SDI",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "전기전자", "sector_l2": "2차전지", "sector_l3": "리튬이온전지",
                "market_cap_tier": "LARGE"
            },
            
            # 자동차
            "005380": {
                "name": "현대차", "name_en": "Hyundai Motor",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "자동차", "sector_l2": "완성차", "sector_l3": "승용차",
                "market_cap_tier": "LARGE"
            },
            "012330": {
                "name": "현대모비스", "name_en": "Hyundai Mobis",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "자동차", "sector_l2": "자동차부품", "sector_l3": "자동차부품",
                "market_cap_tier": "LARGE"
            },
            "000270": {
                "name": "기아", "name_en": "Kia",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "자동차", "sector_l2": "완성차", "sector_l3": "승용차",
                "market_cap_tier": "LARGE"
            },
            
            # 조선
            "009540": {
                "name": "HD한국조선해양", "name_en": "HD Korea Shipbuilding & Offshore Engineering",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "조선", "sector_l2": "조선", "sector_l3": "조선",
                "market_cap_tier": "LARGE"
            },
            
            # 금융
            "055550": {
                "name": "신한지주", "name_en": "Shinhan Financial Group",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "금융", "sector_l2": "은행", "sector_l3": "시중은행",
                "market_cap_tier": "LARGE"
            },
            "323410": {
                "name": "카카오뱅크", "name_en": "KakaoBank",
                "market_type": "DOMESTIC", "exchange": "KRX", "country": "KR",
                "sector_l1": "금융", "sector_l2": "은행", "sector_l3": "인터넷은행",
                "market_cap_tier": "LARGE"
            },
            
            # ============= 해외 주요 종목 =============
            
            # 미국 기술주 (빅테크)
            "AAPL": {
                "name": "Apple Inc", "name_en": "Apple Inc",
                "market_type": "OVERSEAS", "exchange": "NASDAQ", "country": "US",
                "sector_l1": "Technology", "sector_l2": "Consumer Electronics", "sector_l3": "Smartphones",
                "market_cap_tier": "LARGE"
            },
            "MSFT": {
                "name": "Microsoft Corp", "name_en": "Microsoft Corp",
                "market_type": "OVERSEAS", "exchange": "NASDAQ", "country": "US",
                "sector_l1": "Technology", "sector_l2": "Software", "sector_l3": "Operating Systems",
                "market_cap_tier": "LARGE"
            },
            "GOOGL": {
                "name": "Alphabet Inc", "name_en": "Alphabet Inc",
                "market_type": "OVERSEAS", "exchange": "NASDAQ", "country": "US",
                "sector_l1": "Technology", "sector_l2": "Internet Services", "sector_l3": "Search Engine",
                "market_cap_tier": "LARGE"
            },
            "TSLA": {
                "name": "Tesla Inc", "name_en": "Tesla Inc",
                "market_type": "OVERSEAS", "exchange": "NASDAQ", "country": "US",
                "sector_l1": "Consumer Cyclical", "sector_l2": "Auto Manufacturers", "sector_l3": "Electric Vehicles",
                "market_cap_tier": "LARGE"
            },
            "NVDA": {
                "name": "NVIDIA Corp", "name_en": "NVIDIA Corp",
                "market_type": "OVERSEAS", "exchange": "NASDAQ", "country": "US",
                "sector_l1": "Technology", "sector_l2": "Semiconductors", "sector_l3": "Graphics Cards",
                "market_cap_tier": "LARGE"
            },
            "AMZN": {
                "name": "Amazon.com Inc", "name_en": "Amazon.com Inc",
                "market_type": "OVERSEAS", "exchange": "NASDAQ", "country": "US",
                "sector_l1": "Consumer Cyclical", "sector_l2": "Internet Retail", "sector_l3": "E-commerce",
                "market_cap_tier": "LARGE"
            },
            "META": {
                "name": "Meta Platforms Inc", "name_en": "Meta Platforms Inc",
                "market_type": "OVERSEAS", "exchange": "NASDAQ", "country": "US",
                "sector_l1": "Technology", "sector_l2": "Internet Services", "sector_l3": "Social Media",
                "market_cap_tier": "LARGE"
            },
            
            # 미국 기타 주요 종목
            "JPM": {
                "name": "JPMorgan Chase & Co", "name_en": "JPMorgan Chase & Co",
                "market_type": "OVERSEAS", "exchange": "NYSE", "country": "US",
                "sector_l1": "Financial Services", "sector_l2": "Banks", "sector_l3": "Diversified Banks",
                "market_cap_tier": "LARGE"
            },
            "JNJ": {
                "name": "Johnson & Johnson", "name_en": "Johnson & Johnson",
                "market_type": "OVERSEAS", "exchange": "NYSE", "country": "US",
                "sector_l1": "Healthcare", "sector_l2": "Drug Manufacturers", "sector_l3": "General",
                "market_cap_tier": "LARGE"
            },
            "V": {
                "name": "Visa Inc", "name_en": "Visa Inc",
                "market_type": "OVERSEAS", "exchange": "NYSE", "country": "US",
                "sector_l1": "Financial Services", "sector_l2": "Credit Services", "sector_l3": "Credit Services",
                "market_cap_tier": "LARGE"
            }
        }
    
    async def analyze_single_stock(self, symbol: str, stock_info: Dict) -> Optional[Dict[str, Any]]:
        """단일 종목 분석"""
        market_type = stock_info["market_type"]
        name = stock_info["name"]
        sector = f"{stock_info['sector_l1']} > {stock_info['sector_l2']}"
        
        logger.info(f"📊 [{market_type}] {name}({symbol}) 분석 시작 - {sector}")
        
        try:
            start_time = time.time()
            
            # 1. 시장 데이터 수집 (KIS API 기반)
            comprehensive_data = self.provider.get_comprehensive_data(symbol, days=730)
            
            if not comprehensive_data or 'error' in comprehensive_data:
                logger.warning(f"⚠️  {symbol} 데이터 없음: {comprehensive_data.get('error', 'Unknown error')}")
                return None
            
            chart_data = comprehensive_data.get('chart_data')
            if chart_data is None or chart_data.empty:
                logger.warning(f"⚠️  {symbol} 차트 데이터 없음")
                return None
            
            data_days = len(chart_data)
            logger.info(f"   └─ 데이터 수집: {data_days}일 (KIS_API)")
            
            # 2. 기술적 분석 (KIS API 데이터 기반)
            indicators_df = self.technical_analyzer.calculate_all_indicators(chart_data)
            logger.info("기술적 지표 계산 완료: {}개 데이터".format(len(indicators_df)))
            
            # 최신 지표 값들을 딕셔너리로 가져오기
            indicators = self.technical_analyzer.get_latest_indicators(indicators_df)
            logger.info(f"   └─ 기술적 분석: RSI={indicators.get('rsi', 0):.1f}")
            
            # 3. 신호 감지
            signal = self.signal_detector.detect_golden_cross(
                indicators_df, symbol, name
            )
            
            signal_info = self._format_signal_info(signal, symbol)
            logger.info(f"   └─ 신호 감지: {signal_info['type']} (강도: {signal_info['strength']})")
            
            # 4. 백테스팅 (국내 종목만, KIS API 데이터 기반)
            backtest_result = {}
            if market_type == "DOMESTIC":
                try:
                    # Prepare data for backtrader
                    bt_data = self.backtester.prepare_data(chart_data, symbol)
                    backtest_result = self.backtester.run_single_test(
                        bt_data, symbol, stock_info['name'], confirmation_days=1)
                    logger.info(f"   └─ 백테스팅: {backtest_result.get('total_return', 0):.2f}% ({backtest_result.get('trades', 0)}회)")
                except Exception as e:
                    logger.warning(f"   └─ 백테스팅 스킵 ({str(e)[:50]})")
                    backtest_result = self._create_empty_backtest()
            else:
                backtest_result = self._create_empty_backtest()
            
            # 5. 투자 점수 계산
            investment_score = self.calculate_investment_score(
                signal_info, backtest_result, indicators, market_type
            )
            
            recommendation = self.get_recommendation(investment_score)
            analysis_time = int((time.time() - start_time) * 1000)
            
            # 6. 결과 구조화
            result = self._create_analysis_result(
                symbol, stock_info, signal_info, backtest_result,
                indicators, comprehensive_data, investment_score, 
                recommendation, analysis_time
            )
            
            logger.info(f"✅ {name}({symbol}) 완료 - 점수: {investment_score:.1f}, 추천: {recommendation}")
            return result
            
        except Exception as e:
            logger.error(f"❌ {symbol} 분석 실패: {str(e)}")
            return None
    
    def _format_signal_info(self, signal, symbol: str) -> Dict:
        """신호 정보 포맷팅"""
        return {
            "type": signal.signal_type if signal else "NONE",
            "strength": signal.strength if signal else 0,
            "confidence": signal.confidence if signal else "WEAK",
            "confirmation_days": self.signal_detector.get_optimal_confirmation_days(symbol),
            "reason": getattr(signal, 'reason', '') if signal else "신호 없음"
        }
    
    def _create_empty_backtest(self) -> Dict:
        """빈 백테스팅 결과 생성"""
        return {
            "total_return": 0.0,
            "annual_return": 0.0,
            "trades": 0,
            "win_rate": 0.0,
            "max_profit": 0.0,
            "max_loss": 0.0,
            "sharpe_ratio": 0.0,
            "vs_market": 0.0
        }
    
    def _create_analysis_result(self, symbol: str, stock_info: Dict, 
                               signal_info: Dict, backtest_result: Dict,
                               indicators: Dict, comprehensive_data: Dict,
                               investment_score: float, recommendation: str,
                               analysis_time: int) -> Dict:
        """분석 결과 구조화"""
        return {
            # 기본 정보
            "symbol": symbol,
            "symbol_name": stock_info["name"],
            "symbol_name_en": stock_info["name_en"],
            "analyzed_date": date.today().isoformat(),
            
            # 시장 분류
            "market_type": stock_info["market_type"],
            "exchange_code": stock_info["exchange"],
            "country": stock_info["country"],
            "sector_l1": stock_info["sector_l1"],
            "sector_l2": stock_info["sector_l2"], 
            "sector_l3": stock_info["sector_l3"],
            "market_cap_tier": stock_info["market_cap_tier"],
            
            # 투자 평가
            "investment_score": round(investment_score, 2),
            "recommendation": recommendation,
            "risk_level": self.assess_risk_level(indicators, stock_info),
            "confidence_level": self.assess_confidence_level(signal_info, len(comprehensive_data.get('chart_data', pd.DataFrame()))),
            
            # 신호 정보
            "signal": signal_info,
            
            # 백테스팅 결과
            "backtest": backtest_result,
            
            # 현재 시장 데이터
            "market_data": {
                "current_price": int(comprehensive_data.get('chart_data', pd.DataFrame())['close'].iloc[-1]) if not comprehensive_data.get('chart_data', pd.DataFrame()).empty else 0,
                "price_change": float(comprehensive_data.get('chart_data', pd.DataFrame())['close'].iloc[-1] - comprehensive_data.get('chart_data', pd.DataFrame())['close'].iloc[-2]) if len(comprehensive_data.get('chart_data', pd.DataFrame())) > 1 else 0,
                "price_change_rate": float((comprehensive_data.get('chart_data', pd.DataFrame())['close'].iloc[-1] / comprehensive_data.get('chart_data', pd.DataFrame())['close'].iloc[-2] - 1) * 100) if len(comprehensive_data.get('chart_data', pd.DataFrame())) > 1 else 0,
                "volume": int(comprehensive_data.get('chart_data', pd.DataFrame())['volume'].iloc[-1]) if not comprehensive_data.get('chart_data', pd.DataFrame()).empty else 0,
            },
            
            # 기술적 지표
            "indicators": {
                "rsi": round(indicators.get('rsi', 50), 2),
                "sma5": int(indicators.get('sma5', 0)),
                "sma20": int(indicators.get('sma20', 0)),
                "sma60": int(indicators.get('sma60', 0)),
                "sma120": int(indicators.get('sma120', 0)),
                "ema12": int(indicators.get('ema12', 0)),
                "ema26": int(indicators.get('ema26', 0)),
                "macd": round(indicators.get('macd', 0), 2),
                "macd_signal": round(indicators.get('macd_signal', 0), 2),
                "macd_histogram": round(indicators.get('macd_histogram', 0), 2),
                "volatility": round(indicators.get('volatility', 0), 2),
                "volume_ratio": round(indicators.get('volume_ratio', 1.0), 2)
            },
            
            # 메타데이터
            "meta": {
                "analysis_duration_ms": analysis_time,
                "data_source": comprehensive_data.get('data_source', 'KIS_API'),
                "data_quality": self.assess_data_quality(comprehensive_data.get('chart_data', pd.DataFrame())),
                "data_period_days": len(comprehensive_data.get('chart_data', pd.DataFrame())),
                "analysis_engine_version": "1.0.0",
                "created_at": datetime.now().isoformat()
            }
        }
    
    def calculate_investment_score(self, signal: Dict, backtest: Dict, 
                                   indicators: Dict, market_type: str) -> float:
        """투자 적합성 점수 계산 (0-100점)"""
        score = 50.0  # 기본 점수
        
        # 신호 점수 (0-25점)
        if signal['type'] == 'GOLDEN_CROSS':
            score += 15 + (signal['strength'] * 0.1)
        elif signal['type'] == 'DEAD_CROSS':
            score -= 10
        
        # 백테스팅 점수 (국내만, -15~+15점)
        if market_type == "DOMESTIC" and backtest.get('total_return', 0) != 0:
            score += min(15, max(-15, backtest.get('total_return', 0) * 5))
        
        # RSI 점수 (-10~+10점)
        rsi = indicators.get('rsi', 50)
        if 30 <= rsi <= 70:
            score += 8
        elif 20 <= rsi < 30 or 70 < rsi <= 80:
            score += 3
        elif rsi < 20 or rsi > 80:
            score -= 8
        
        # 추세 점수 (SMA 배열, -10~+10점)
        sma5 = indicators.get('sma5', 0)
        sma20 = indicators.get('sma20', 0)
        sma60 = indicators.get('sma60', 0)
        
        if sma5 > sma20 > sma60:
            score += 10  # 상승 추세
        elif sma5 > sma20:
            score += 5   # 단기 상승
        elif sma5 < sma20 < sma60:
            score -= 8   # 하락 추세
        
        # 변동성 점수 (-5~+5점)
        volatility = indicators.get('volatility', 2.0)
        if 1.0 <= volatility <= 3.0:
            score += 5  # 적정 변동성
        elif volatility > 5.0:
            score -= 5  # 과도한 변동성
        
        return max(0, min(100, score))
    
    def get_recommendation(self, score: float) -> str:
        """점수 기반 투자 추천"""
        if score >= 75:
            return "매수추천"
        elif score >= 60:
            return "매수고려"
        elif score >= 45:
            return "보유"
        elif score >= 30:
            return "매수주의"
        else:
            return "매수비추천"
    
    def assess_risk_level(self, indicators: Dict, stock_info: Dict) -> str:
        """리스크 레벨 평가"""
        volatility = indicators.get('volatility', 2.0)
        market_cap_tier = stock_info['market_cap_tier']
        
        if volatility > 4.0 or market_cap_tier == 'SMALL':
            return "HIGH"
        elif volatility > 2.5 or market_cap_tier == 'MID':
            return "MEDIUM"
        else:
            return "LOW"
    
    def assess_confidence_level(self, signal: Dict, data_days: int) -> str:
        """신뢰도 레벨 평가"""
        if data_days >= 500 and signal['confidence'] == 'CONFIRMED':
            return "HIGH"
        elif data_days >= 300 and signal['confidence'] in ['CONFIRMED', 'TENTATIVE']:
            return "MEDIUM"
        else:
            return "LOW"
    
    def assess_data_quality(self, df: pd.DataFrame) -> str:
        """데이터 품질 평가"""
        days = len(df)
        if days >= 500:
            return "EXCELLENT"
        elif days >= 300:
            return "GOOD"
        elif days >= 150:
            return "FAIR"
        else:
            return "POOR"
    
    async def run_comprehensive_analysis(self, target_symbols: Optional[List[str]] = None) -> List[Dict]:
        """종합 분석 실행"""
        logger.info("🚀 종합 주식 분석 시작")
        
        # 대상 종목 결정
        if target_symbols:
            symbols_to_analyze = target_symbols
        else:
            symbols_to_analyze = list(self.symbol_registry.keys())
        
        logger.info(f"📊 분석 대상: {len(symbols_to_analyze)}개 종목")
        
        # 시장별 집계
        domestic_count = sum(1 for s in symbols_to_analyze if self.symbol_registry[s]['market_type'] == 'DOMESTIC')
        overseas_count = len(symbols_to_analyze) - domestic_count
        
        logger.info(f"   └─ 국내: {domestic_count}개, 해외: {overseas_count}개")
        
        # 분석 실행
        all_results = []
        failed_symbols = []
        
        for i, symbol in enumerate(symbols_to_analyze, 1):
            stock_info = self.symbol_registry[symbol]
            
            logger.info(f"\n[{i}/{len(symbols_to_analyze)}] 진행률: {i/len(symbols_to_analyze)*100:.1f}%")
            
            try:
                result = await self.analyze_single_stock(symbol, stock_info)
                
                if result:
                    all_results.append(result)
                else:
                    failed_symbols.append(symbol)
                
                # API 호출 제한 고려 (0.1초 대기)
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ {symbol} 분석 중 오류: {str(e)}")
                failed_symbols.append(symbol)
        
        # 결과 요약
        self._print_analysis_summary(all_results, failed_symbols)
        
        # 결과 저장
        await self._save_results(all_results)
        
        return all_results
    
    def _print_analysis_summary(self, results: List[Dict], failed_symbols: List[str]):
        """분석 결과 요약 출력"""
        logger.info(f"\n✅ 종합 분석 완료!")
        logger.info(f"   📊 성공: {len(results)}개")
        logger.info(f"   ❌ 실패: {len(failed_symbols)}개")
        
        if failed_symbols:
            logger.info(f"   실패 종목: {', '.join(failed_symbols)}")
        
        if results:
            # 시장별 집계
            domestic_results = [r for r in results if r['market_type'] == 'DOMESTIC']
            overseas_results = [r for r in results if r['market_type'] == 'OVERSEAS']
            
            # 점수 통계
            scores = [r['investment_score'] for r in results]
            avg_score = sum(scores) / len(scores)
            
            logger.info(f"\n📈 분석 통계:")
            logger.info(f"   🇰🇷 국내: {len(domestic_results)}개")
            logger.info(f"   🌍 해외: {len(overseas_results)}개")
            logger.info(f"   📊 평균 점수: {avg_score:.1f}점")
            
            # 신호 집계
            golden_cross = len([r for r in results if r['signal']['type'] == 'GOLDEN_CROSS'])
            dead_cross = len([r for r in results if r['signal']['type'] == 'DEAD_CROSS'])
            
            logger.info(f"   ⚡ 골든크로스: {golden_cross}개")
            logger.info(f"   ❌ 데드크로스: {dead_cross}개")
            
            # 추천 집계
            buy_recommend = len([r for r in results if r['recommendation'] == '매수추천'])
            buy_consider = len([r for r in results if r['recommendation'] == '매수고려'])
            
            logger.info(f"   🟢 매수추천: {buy_recommend}개")
            logger.info(f"   🟡 매수고려: {buy_consider}개")
    
    async def _save_results(self, results: List[Dict]):
        """분석 결과 저장"""
        today_str = date.today().strftime("%Y%m%d")
        
        # JSON 파일 저장
        json_file = self._save_to_json(results, today_str)
        
        # PostgreSQL 저장 (나중에 구현)
        # await self._save_to_database(results)
        
        logger.info(f"💾 결과 저장 완료: {json_file}")
    
    def _save_to_json(self, results: List[Dict], date_str: str) -> str:
        """JSON 파일로 저장"""
        # 결과 디렉토리 생성
        results_dir = Path("analysis_results")
        results_dir.mkdir(exist_ok=True)
        
        # 파일 경로
        json_file = results_dir / f"comprehensive_analysis_{date_str}.json"
        
        # 메타데이터와 함께 저장
        output_data = {
            "analysis_info": {
                "analysis_date": date.today().isoformat(),
                "total_stocks": len(results),
                "analysis_engine": "ComprehensiveBatchAnalyzer",
                "version": "1.0.0",
                "created_at": datetime.now().isoformat()
            },
            "market_summary": self._create_market_summary(results),
            "sector_summary": self._create_sector_summary(results),
            "analysis_results": results
        }
        
        # JSON 저장
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return str(json_file)
    
    def _create_market_summary(self, results: List[Dict]) -> Dict:
        """시장별 요약 생성"""
        domestic_results = [r for r in results if r['market_type'] == 'DOMESTIC']
        overseas_results = [r for r in results if r['market_type'] == 'OVERSEAS']
        
        def calc_summary(market_results):
            if not market_results:
                return {"count": 0}
            
            scores = [r['investment_score'] for r in market_results]
            return {
                "count": len(market_results),
                "avg_score": round(sum(scores) / len(scores), 1),
                "max_score": max(scores),
                "min_score": min(scores),
                "golden_cross_count": len([r for r in market_results if r['signal']['type'] == 'GOLDEN_CROSS']),
                "buy_recommend_count": len([r for r in market_results if r['recommendation'] == '매수추천'])
            }
        
        return {
            "DOMESTIC": calc_summary(domestic_results),
            "OVERSEAS": calc_summary(overseas_results),
            "TOTAL": calc_summary(results)
        }
    
    def _create_sector_summary(self, results: List[Dict]) -> Dict:
        """섹터별 요약 생성"""
        sector_groups = {}
        
        for result in results:
            sector = result['sector_l1']
            if sector not in sector_groups:
                sector_groups[sector] = []
            sector_groups[sector].append(result)
        
        sector_summary = {}
        for sector, sector_results in sector_groups.items():
            scores = [r['investment_score'] for r in sector_results]
            
            sector_summary[sector] = {
                "count": len(sector_results),
                "avg_score": round(sum(scores) / len(scores), 1),
                "max_score": max(scores),
                "golden_cross_count": len([r for r in sector_results if r['signal']['type'] == 'GOLDEN_CROSS']),
                "top_stock": max(sector_results, key=lambda x: x['investment_score'])['symbol']
            }
        
        return sector_summary
    
    def run_comprehensive_analysis_sync(self):
        """Airflow용 동기 실행 함수"""
        try:
            logger.info("🚀 Airflow 동기 분석 시작...")
            
            results = []
            for stock in self.stock_list:
                result = self.analyze_single_stock(stock)
                if result:
                    results.append(result)
            
            # 결과 요약
            summary = self._create_market_summary(results)
            
            # 전체 결과 구성
            final_results = {
                "analysis_info": {
                    "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                    "total_stocks": len(results),
                    "analysis_engine": "ComprehensiveBatchAnalyzer",
                    "version": "1.0.0",
                    "created_at": datetime.now().isoformat()
                },
                "market_summary": summary,
                "sector_summary": self._create_sector_summary(results),
                "analysis_results": results
            }
            
            # JSON 파일 저장
            self.save_to_json(final_results)
            
            logger.info(f"✅ Airflow 분석 완료: {len(results)}개 종목")
            return final_results
            
        except Exception as e:
            logger.error(f"❌ Airflow 분석 오류: {e}")
            raise

# 실행 스크립트
async def main():
    """메인 실행 함수"""
    analyzer = ComprehensiveBatchAnalyzer()
    
    # 특정 종목만 테스트하고 싶다면:
    # test_symbols = ["005930", "000660", "AAPL", "MSFT"]
    # results = await analyzer.run_comprehensive_analysis(test_symbols)
    
    # 전체 종목 분석
    results = await analyzer.run_comprehensive_analysis()
    
    print(f"\n🎉 분석 완료! 총 {len(results)}개 종목 분석됨")

if __name__ == "__main__":
    asyncio.run(main())