"""
재무지표 계산 모듈

키움 API와 DART API를 통합하여 주식 분석에 필요한 모든 재무지표를 계산합니다.
Google Sheets의 VLOOKUP 계산에 필요한 데이터를 제공합니다.
"""

import sys
from pathlib import Path
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import json

# Handle both relative and absolute imports for different execution contexts
try:
    from ...functions.stock import fn_ka10001
    from ...config.settings import settings
except ImportError:
    # If relative imports fail, add src to path and use absolute imports
    src_path = Path(__file__).parent.parent.parent
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    from kiwoom_api.functions.stock import fn_ka10001
    from kiwoom_api.config.settings import settings


# 실제 키움 API 함수들과 DART API 클라이언트 임포트
try:
    from ..functions.historical import fn_ka10005
    from ..functions.stock_institutional_trend import fn_ka10045
    from ..external.dart_client import DARTClient
except ImportError:
    from kiwoom_api.functions.historical import fn_ka10005
    from kiwoom_api.functions.stock_institutional_trend import fn_ka10045
    from kiwoom_api.external.dart_client import DARTClient


class FinancialDataCollector:
    """재무 데이터 수집기"""
    
    def __init__(self):
        self.kiwoom_api_base = settings.kiwoom_base_url
        self.dart_api_key = getattr(settings, 'DART_API_KEY', None)
        self.cache = {}
        self.cache_ttl = 300  # 5분 캐시
        self.dart_client = None  # DART 클라이언트 (지연 초기화)
    
    async def _get_dart_client(self) -> Optional[DARTClient]:
        """DART 클라이언트 인스턴스 획득 (지연 초기화)"""
        if self.dart_client is None and self.dart_api_key:
            try:
                self.dart_client = DARTClient(self.dart_api_key)
            except Exception as e:
                print(f"DART 클라이언트 초기화 실패: {e}")
                return None
        return self.dart_client
    
    async def get_stock_basic_info(self, stock_code: str) -> Dict[str, Any]:
        """
        키움 ka10001 API를 통한 기본 주식 정보 수집
        
        Args:
            stock_code: 6자리 종목코드
            
        Returns:
            기본 주식 정보 딕셔너리
        """
        cache_key = f"basic_info_{stock_code}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        # 실제 키움 API ka10001로 기본 주식 정보 수집
        
        try:
            # ka10001: 주식기본정보요청 (실제 API 호출)
            basic_info = await fn_ka10001(data={'stk_cd': stock_code})
            
            if basic_info and basic_info.get('Code') == 200:
                body = basic_info.get('Body', {})
                
                # 키움 API 응답에서 올바른 필드명 사용
                # cur_prc: 현재가, 250hgst: 250일(약 52주) 최고가, 250lwst: 250일(약 52주) 최저가
                def parse_price(price_str):
                    """가격 문자열 파싱 (+70600 -> 70600.0)"""
                    if not price_str:
                        return 0.0
                    return float(str(price_str).replace('+', '').replace('-', '').replace(',', ''))
                
                current_price = parse_price(body.get('cur_prc', '0'))
                high_52w = parse_price(body.get('250hgst', '0'))  # 250일 최고가 (약 52주)
                low_52w = parse_price(body.get('250lwst', '0'))   # 250일 최저가 (약 52주)
                
                result = {
                    'stock_code': stock_code,
                    'stock_name': body.get('stk_nm', ''),
                    'current_price': current_price,
                    'per': float(body.get('per', 0)),
                    'pbr': float(body.get('pbr', 0)),
                    'roe': float(body.get('roe', 0)),
                    'dividend_yield': float(body.get('eps', 0)) / current_price * 100 if current_price > 0 else 0,  # EPS/현재가 * 100
                    'market_cap': float(body.get('mac', 0)) * 100000000,  # 시가총액(백만원 단위)
                    'volume': int(str(body.get('trde_qty', '0')).replace(',', '') or '0'),
                    'high_52w': high_52w,
                    'low_52w': low_52w
                }
                
                # 52주 대비 위치 계산 (Google Sheets 공식에 맞게)
                # 예: -40%는 최저가 대비 40% 하락 의미
                if high_52w > 0 and low_52w > 0:
                    # 옵션 1: 최저가 대비 변화율 (Google Sheets 공식에 맞는 방식)
                    position_52w_low_based = ((current_price - low_52w) / low_52w) * 100 - 100  # 최저가 대비 %
                    
                    # 옵션 2: 전통적인 52주 위치 (참고용)
                    position_52w_range = ((current_price - low_52w) / (high_52w - low_52w)) * 100
                    
                    # Google Sheets 공식에서 -40% 등의 음수값을 기대하므로 옵션 1 사용
                    result['position_52w'] = position_52w_low_based
                    print(f"디버깅 - 52주 데이터: current={current_price}, high={high_52w}, low={low_52w}")
                    print(f"디버깅 - 최저가 대비: {position_52w_low_based:.2f}% | 전통적 위치: {position_52w_range:.2f}%")
                else:
                    result['position_52w'] = 0
                    print(f"52주 데이터 부족: high={high_52w}, low={low_52w}")
                
                # 캐시 저장
                self.cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                return result
        except Exception as e:
            print(f"Error fetching basic info for {stock_code}: {e}")
            
        # 기본값 반환 (알 수 없는 종목)
        return {
            'stock_code': stock_code,
            'stock_name': f"종목{stock_code}",
            'current_price': 10000.0,
            'per': 10.0,
            'pbr': 1.0,
            'roe': 8.0,
            'dividend_yield': 1.0,
            'market_cap': 1000000000,
            'volume': 100000,
            'high_52w': 12000.0,
            'low_52w': 8000.0
        }
    
    async def get_historical_data(self, stock_code: str, period_days: int = 365) -> Dict[str, Any]:
        """
        키움 ka10005 API를 통한 과거 시세 데이터 수집
        
        Args:
            stock_code: 6자리 종목코드
            period_days: 데이터 수집 기간 (일)
            
        Returns:
            과거 시세 데이터 딕셔너리
        """
        cache_key = f"historical_{stock_code}_{period_days}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # ka10005: 과거시세조회 (일봉)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=period_days)).strftime('%Y%m%d')
            
            # fn_ka10005 함수 인터페이스에 맞게 호출
            request_data = {
                'stk_cd': stock_code,
                'strt_dt': start_date,
                'end_dt': end_date,
                'period_div_cd': '1'  # 1: 일봉
            }
            historical_data = await fn_ka10005(request_data)
            
            if historical_data and historical_data.get('Code') == 200:
                body = historical_data.get('Body', {})
                data_list = body.get('output2', [])
                if data_list:
                    # 최근 데이터부터 정렬
                    data_list.sort(key=lambda x: x.get('stck_bsop_date', ''), reverse=True)
                    
                    # 현재년도와 전년도 데이터 추출
                    current_year = datetime.now().year
                    current_year_data = [d for d in data_list if d.get('stck_bsop_date', '')[:4] == str(current_year)]
                    previous_year_data = [d for d in data_list if d.get('stck_bsop_date', '')[:4] == str(current_year-1)]
                    
                    # RSI 계산을 위한 가격 데이터
                    prices = [float(d.get('stck_clpr', 0)) for d in data_list]
                    volumes = [int(d.get('acml_vol', 0)) for d in data_list]
                    
                    result = {
                        'stock_code': stock_code,
                        'current_price': float(data_list[0].get('stck_clpr', 0)) if data_list else 0,
                        'prices': prices[:100],  # 최근 100일 가격
                        'volumes': volumes[:100],  # 최근 100일 거래량
                        'rsi': self._calculate_rsi(prices[:14]) if len(prices) >= 14 else 50,
                        'obv': self._calculate_obv(prices[:20], volumes[:20]) if len(prices) >= 20 else 0,
                        'current_year_data': current_year_data,
                        'previous_year_data': previous_year_data
                    }
                    
                    # 52주 대비 현재 위치 계산
                    basic_info = await self.get_stock_basic_info(stock_code)
                    if basic_info.get('high_52w') and basic_info.get('low_52w'):
                        high_52w = basic_info['high_52w']
                        low_52w = basic_info['low_52w']
                        current_price = basic_info['current_price']
                        
                        if high_52w != low_52w:
                            position_52w = ((current_price - low_52w) / (high_52w - low_52w) - 0.5) * 200
                            result['position_52w'] = position_52w
                        else:
                            result['position_52w'] = 0
                    
                    # 캐시 저장
                    self.cache[cache_key] = {
                        'data': result,
                        'timestamp': datetime.now()
                    }
                    
                    return result
        except Exception as e:
            print(f"Error fetching historical data for {stock_code}: {e}")
            return {}
        
        return {}
    
    async def get_institutional_data(self, stock_code: str) -> Dict[str, Any]:
        """
        키움 ka10045 API를 통한 기관/외국인 데이터 수집
        
        Args:
            stock_code: 6자리 종목코드
            
        Returns:
            기관/외국인 데이터 딕셔너리
        """
        cache_key = f"institutional_{stock_code}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # ka10045: 종목별기관매매추이요청
            # 최근 30일간의 기관매매 추이 조회
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
            
            request_data = {
                'stk_cd': stock_code,
                'strt_dt': start_date,
                'end_dt': end_date
            }
            institutional_data = await fn_ka10045(request_data)
            
            if institutional_data and institutional_data.get('Code') == 200:
                body = institutional_data.get('Body', {})
                # output2 배열에서 최근 데이터 추출
                output_data = body.get('output2', [])
                if output_data:
                    # 최근 데이터 사용 (첫 번째 데이터)
                    latest_data = output_data[0]
                    result = {
                        'stock_code': stock_code,
                        'foreign_ownership': float(latest_data.get('frgn_ntby_qty', 0)),  # 외국인 순매수수량
                        'foreign_ratio': float(latest_data.get('frgn_hldn_rt', 0)),  # 외국인 보유비율
                        'institutional_ownership': float(latest_data.get('inst_ntby_qty', 0)),  # 기관 순매수수량
                        'institutional_ratio': float(latest_data.get('inst_hldn_rt', 0)),  # 기관 보유비율
                        'listed_shares': float(latest_data.get('lstg_stqt', 0))  # 상장주식수
                    }
                else:
                    # 데이터가 없으면 기본값 설정
                    result = {
                        'stock_code': stock_code,
                        'foreign_ownership': 0.0,
                        'foreign_ratio': 0.0,
                        'institutional_ownership': 0.0,
                        'institutional_ratio': 0.0,
                        'listed_shares': 0.0
                    }
                
                # 최근 1-3개월 기관/외국인 순매수 비율 계산 (상장주식수 대비)
                if result['listed_shares'] > 0:
                    net_buy_ratio = (result['foreign_ownership'] + result['institutional_ownership']) / result['listed_shares'] * 100
                    result['institutional_supply'] = net_buy_ratio
                else:
                    result['institutional_supply'] = 0
                
                # 캐시 저장
                self.cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                return result
        except Exception as e:
            print(f"Error fetching institutional data for {stock_code}: {e}")
            return {}
        
        return {}
    
    async def get_dart_financial_data(self, stock_code: str) -> Dict[str, Any]:
        """
        DART API를 통한 상세 재무 데이터 수집
        
        Args:
            stock_code: 6자리 종목코드
            
        Returns:
            DART 재무 데이터 딕셔너리
        """
        if not self.dart_api_key:
            return {}
        
        cache_key = f"dart_{stock_code}"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]['data']
        
        try:
            # 실제 DART 클라이언트 사용
            dart_client = await self._get_dart_client()
            if not dart_client:
                print(f"DART 클라이언트가 없어 {stock_code} DART 데이터 수집을 건너뜁니다")
                return {}
            
            # 최근년도 재무제표 데이터 조회 (사업보고서)
            current_year = datetime.now().year - 1  # 전년도 사업보고서
            financial_data = await dart_client.get_financial_statement(
                stock_code, current_year, "11011"  # 사업보고서
            )
            
            if financial_data:
                # DART 클라이언트에서 이미 계산된 지표들을 매핑
                result = {
                    'stock_code': stock_code,
                    'current_sales': financial_data.get('revenue_current', 0),  # 당기매출액
                    'previous_sales': financial_data.get('revenue_previous', 0),  # 전기매출액
                    'current_profit': financial_data.get('operating_profit_current', 0),  # 당기영업이익
                    'previous_profit': financial_data.get('operating_profit_previous', 0),  # 전기영업이익
                    'operating_margin': financial_data.get('operating_margin', 0),  # 영업이익률
                    'retention_ratio': financial_data.get('retention_ratio', 0),  # 유보율
                    'debt_ratio': financial_data.get('debt_ratio', 0),  # 부채비율
                    'interest_coverage_ratio': financial_data.get('interest_coverage_ratio', None),  # 이자보상배율
                    'roe': financial_data.get('roe', 0),  # ROE
                    'roa': financial_data.get('roa', 0),  # ROA
                    'total_assets': financial_data.get('total_assets', 0),  # 자산총계
                    'total_equity': financial_data.get('total_equity', 0),  # 자본총계
                    'net_income': financial_data.get('net_income', 0)  # 당기순이익
                }
                
                # 매출 성장률 계산
                if result['previous_sales'] > 0:
                    result['sales_growth_rate'] = (
                        (result['current_sales'] - result['previous_sales']) / result['previous_sales'] * 100
                    )
                else:
                    result['sales_growth_rate'] = 0
                
                # 영업이익 성장률 계산  
                if result['previous_profit'] > 0:
                    result['profit_growth_rate'] = (
                        (result['current_profit'] - result['previous_profit']) / result['previous_profit'] * 100
                    )
                else:
                    result['profit_growth_rate'] = 0
                
                print(f"DART 데이터 수집 성공: {stock_code}, 매출액: {result['current_sales']:,.0f}천원, ROE: {result['roe']:.2f}%")
                
                # 캐시 저장
                self.cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
                
                return result
            
        except Exception as e:
            print(f"DART 데이터 수집 실패 for {stock_code}: {e}")
            # DART 데이터 수집 실패 시 빈 결과 반환 (기본값으로 처리됨)
            return {}
        
        return {}
    
    async def get_comprehensive_data(self, stock_code: str) -> Dict[str, Any]:
        """
        종합 데이터 수집 (키움 API + DART API 통합)
        
        Args:
            stock_code: 6자리 종목코드
            
        Returns:
            종합 주식 분석 데이터
        """
        # 병렬로 모든 데이터 수집
        basic_info_task = self.get_stock_basic_info(stock_code)
        historical_task = self.get_historical_data(stock_code)
        institutional_task = self.get_institutional_data(stock_code)
        dart_task = self.get_dart_financial_data(stock_code)
        
        basic_info, historical, institutional, dart_data = await asyncio.gather(
            basic_info_task, historical_task, institutional_task, dart_task,
            return_exceptions=True
        )
        
        # 예외 처리
        basic_info = basic_info if not isinstance(basic_info, Exception) else {}
        historical = historical if not isinstance(historical, Exception) else {}
        institutional = institutional if not isinstance(institutional, Exception) else {}
        dart_data = dart_data if not isinstance(dart_data, Exception) else {}
        
        # 통합 데이터 구성
        comprehensive_data = {
            'stock_code': stock_code,
            'stock_name': basic_info.get('stock_name', ''),
            
            # 기본 주식 정보 (키움 API)
            'current_price': basic_info.get('current_price', 0),
            'per': basic_info.get('per', 0),
            'pbr': basic_info.get('pbr', 0),
            'roe': basic_info.get('roe', 0),
            'dividend_yield': basic_info.get('dividend_yield', 0),
            'market_cap': basic_info.get('market_cap', 0),
            'volume': basic_info.get('volume', 0),
            
            # 기술적 지표 (키움 API + 계산)
            'rsi_value': historical.get('rsi', 50),
            'obv_value': historical.get('obv', 0),
            'obv_satisfied': historical.get('obv', 0) > 0,  # 단순화된 OBV 판정
            'position_52w': basic_info.get('position_52w', historical.get('position_52w', 0)),  # basic_info에서 우선 가져오기
            'sentiment_percentage': 50,  # TODO: 투자심리도 계산 로직 필요
            
            # 기관/외국인 데이터 (키움 API)
            'foreign_ownership': institutional.get('foreign_ownership', 0),
            'foreign_ratio': institutional.get('foreign_ratio', 0),
            'institutional_ownership': institutional.get('institutional_ownership', 0),
            'institutional_ratio': institutional.get('institutional_ratio', 0),
            'institutional_supply': institutional.get('institutional_supply', 0),
            
            # 재무 데이터 (DART API 우선, 키움 API 보완)
            'current_sales': dart_data.get('current_sales', 0),
            'previous_sales': dart_data.get('previous_sales', 1),  # 0으로 나누기 방지
            'current_profit': dart_data.get('current_profit', 0),
            'previous_profit': dart_data.get('previous_profit', 0),
            'operating_margin': dart_data.get('operating_margin', 0),
            'retention_ratio': dart_data.get('retention_ratio', 0),
            'debt_ratio': dart_data.get('debt_ratio', 0),
            'interest_coverage_ratio': dart_data.get('interest_coverage_ratio'),
            
            # 재료 관련 (사용자 입력 또는 뉴스 API 연동 필요)
            'has_imminent_event': False,
            'is_leading_theme': False,
            'has_earnings_surprise': False,
            'has_unfaithful_disclosure': False,
            'has_negative_news': False,
            
            # 메타 정보
            'data_collection_time': datetime.now(),
            'data_sources': {
                'basic_info': 'Kiwoom ka10001',
                'historical': 'Kiwoom ka10005',
                'institutional': 'Kiwoom ka10045',
                'financial': 'DART API' if dart_data else 'Kiwoom API',
                'technical': 'Calculated'
            }
        }
        
        # 디버깅: position_52w 전달 확인
        print(f"디버깅 - comprehensive_data position_52w: {comprehensive_data['position_52w']}, basic_info에서: {basic_info.get('position_52w', 'None')}")
        
        return comprehensive_data
    
    def _calculate_rsi(self, prices: list, period: int = 14) -> float:
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50.0
        
        gains = []
        losses = []
        
        for i in range(1, len(prices)):
            change = prices[i-1] - prices[i]  # 최신 데이터가 앞에 있음
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        if len(gains) < period:
            return 50.0
        
        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi, 2)
    
    def _calculate_obv(self, prices: list, volumes: list) -> float:
        """OBV (On Balance Volume) 계산"""
        if len(prices) < 2 or len(volumes) < 2:
            return 0.0
        
        obv = 0
        for i in range(1, min(len(prices), len(volumes))):
            if prices[i-1] > prices[i]:  # 가격 상승
                obv += volumes[i]
            elif prices[i-1] < prices[i]:  # 가격 하락
                obv -= volumes[i]
            # 가격 동일하면 OBV 변화 없음
        
        return obv
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """캐시 유효성 검사"""
        if cache_key not in self.cache:
            return False
        
        cache_time = self.cache[cache_key]['timestamp']
        return (datetime.now() - cache_time).seconds < self.cache_ttl


# 테스트 함수
async def test_financial_data_collector():
    """재무 데이터 수집기 테스트"""
    collector = FinancialDataCollector()
    
    print("=== 재무 데이터 수집기 테스트 ===")
    
    test_stock_code = "005930"  # 삼성전자
    
    print(f"\n{test_stock_code} 종합 데이터 수집 중...")
    comprehensive_data = await collector.get_comprehensive_data(test_stock_code)
    
    print(f"종목명: {comprehensive_data.get('stock_name')}")
    print(f"현재가: {comprehensive_data.get('current_price'):,.0f}원")
    print(f"PER: {comprehensive_data.get('per')}")
    print(f"PBR: {comprehensive_data.get('pbr')}")
    print(f"ROE: {comprehensive_data.get('roe')}%")
    print(f"배당수익률: {comprehensive_data.get('dividend_yield')}%")
    print(f"RSI: {comprehensive_data.get('rsi_value')}")
    print(f"52주 대비 위치: {comprehensive_data.get('position_52w'):.1f}%")
    print(f"외국인 비중: {comprehensive_data.get('foreign_ratio')}%")
    print(f"기관 비중: {comprehensive_data.get('institutional_ratio')}%")
    
    print(f"\n데이터 소스:")
    for source, api in comprehensive_data.get('data_sources', {}).items():
        print(f"  {source}: {api}")
    
    print("\n✅ 테스트 완료!")


if __name__ == "__main__":
    asyncio.run(test_financial_data_collector())