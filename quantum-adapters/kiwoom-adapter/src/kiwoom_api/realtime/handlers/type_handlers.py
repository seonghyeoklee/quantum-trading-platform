"""
타입별 실시간 데이터 핸들러 구현
"""

from typing import Dict, Any, Optional
from .base_handler import BaseRealtimeHandler
from ..models.realtime_data import RealtimeData
from ..utils.field_mapping import get_readable_data, is_price_field, is_volume_field


class StockQuoteHandler(BaseRealtimeHandler):
    """00: 주식호가잔량 핸들러"""
    
    def __init__(self):
        super().__init__("00")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식호가잔량 데이터 처리"""
        try:
            # 주요 필드 추출
            symbol = data.item
            current_price = data.get_field_value("10")
            best_ask = data.get_field_value("27")
            best_bid = data.get_field_value("28")
            symbol_name = data.get_field_value("302")
            
            # 처리된 데이터 구성
            processed_data = {
                "type": "stock_quote",
                "symbol": symbol,
                "symbol_name": symbol_name,
                "current_price": current_price,
                "best_ask_price": best_ask,
                "best_bid_price": best_bid,
                "raw_data": data.values,
                "readable_data": get_readable_data(data.values)
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            print(f"📊 주식호가잔량 ({symbol}): 현재가={current_price}, 매도호가={best_ask}, 매수호가={best_bid}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 주식호가잔량 처리 오류: {e}")
            return None


class StockExecutionHandler(BaseRealtimeHandler):
    """0B: 주식체결 핸들러 (공식 가이드 완전 구현)"""
    
    def __init__(self):
        super().__init__("0B")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식체결 데이터 처리 (모든 필드 지원)"""
        try:
            # 기본 정보
            symbol = data.item
            symbol_name = data.get_field_value("302")
            
            # 가격 정보
            current_price = data.get_field_value("10")
            change = data.get_field_value("11")
            change_rate = data.get_field_value("12")
            change_sign = data.get_field_value("25")
            
            # 시가/고가/저가
            open_price = data.get_field_value("16")
            high_price = data.get_field_value("17")
            low_price = data.get_field_value("18")
            
            # 호가 정보
            best_ask = data.get_field_value("27")
            best_bid = data.get_field_value("28")
            
            # 거래량 정보
            volume = data.get_field_value("15")
            total_volume = data.get_field_value("13")
            total_amount = data.get_field_value("14")
            
            # 체결 상세 정보
            execution_time = data.get_field_value("20")
            sell_volume = data.get_field_value("1030")
            buy_volume = data.get_field_value("1031")
            buy_ratio = data.get_field_value("1032")
            
            # 시장 정보
            market_type = data.get_field_value("290")
            exchange = data.get_field_value("9081")
            market_cap = data.get_field_value("311")
            
            # 처리된 데이터 구성 (모든 주요 필드 포함)
            processed_data = {
                "type": "stock_execution",
                "symbol": symbol,
                "symbol_name": symbol_name,
                
                # 가격 정보
                "current_price": current_price,
                "change": change,
                "change_rate": change_rate,
                "change_sign": change_sign,
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                
                # 호가 정보
                "best_ask_price": best_ask,
                "best_bid_price": best_bid,
                
                # 거래량 정보
                "volume": volume,
                "total_volume": total_volume,
                "total_amount": total_amount,
                "sell_volume": sell_volume,
                "buy_volume": buy_volume,
                "buy_ratio": buy_ratio,
                
                # 시장 정보
                "execution_time": execution_time,
                "market_type": market_type,
                "exchange": exchange,
                "market_cap": market_cap,
                
                # 전체 데이터
                "raw_data": data.values,
                "readable_data": get_readable_data(data.values),
                "field_count": len(data.values)
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 향상된 로깅 (주요 정보만)
            market_desc = self._get_market_description(market_type)
            sign_desc = self._get_change_sign_description(change_sign)
            
            print(f"📈 주식체결 ({symbol}): {current_price}원 {sign_desc}{change}({change_rate}%) "
                  f"거래량={volume} 매수비율={buy_ratio}% 시장={market_desc} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 주식체결 처리 오류: {e}")
            return None
    
    def _get_market_description(self, market_type: str) -> str:
        """장구분 코드를 설명으로 변환"""
        market_map = {
            "1": "장전시간외",
            "2": "장중",
            "3": "장후시간외"
        }
        return market_map.get(market_type, f"알수없음({market_type})")
    
    def _get_change_sign_description(self, change_sign: str) -> str:
        """전일대비기호를 설명으로 변환"""
        if not change_sign:
            return ""
        
        # 키움 전일대비기호 매핑 (실제 값에 따라 조정 필요)
        sign_map = {
            "1": "↑",  # 상승
            "2": "↓",  # 하락
            "3": "→",  # 보합
            "4": "↑",  # 상한가
            "5": "↓",  # 하한가
        }
        return sign_map.get(change_sign, change_sign)


class StockMomentumHandler(BaseRealtimeHandler):
    """0A: 주식기세 핸들러"""
    
    def __init__(self):
        super().__init__("0A")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식기세 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item
            symbol_name = data.get_field_value("302")
            
            # 가격 정보
            current_price = data.get_field_value("10")
            change = data.get_field_value("11")
            change_rate = data.get_field_value("12")
            change_sign = data.get_field_value("25")
            
            # 시가/고가/저가
            open_price = data.get_field_value("16")
            high_price = data.get_field_value("17")
            low_price = data.get_field_value("18")
            
            # 호가 정보
            best_ask = data.get_field_value("27")
            best_bid = data.get_field_value("28")
            
            # 거래량 정보
            total_volume = data.get_field_value("13")
            total_amount = data.get_field_value("14")
            
            # 거래 관련 정보
            volume_ratio = data.get_field_value("26")
            amount_change = data.get_field_value("29")
            volume_ratio_percent = data.get_field_value("30")
            turnover_rate = data.get_field_value("31")
            trading_cost = data.get_field_value("32")
            market_cap = data.get_field_value("311")
            
            # 시간 정보
            upper_limit_time = data.get_field_value("567")
            lower_limit_time = data.get_field_value("568")
            
            # 처리된 데이터 구성
            processed_data = {
                "type": "stock_execution_processing",
                "symbol": symbol,
                "symbol_name": symbol_name,
                
                # 가격 정보
                "current_price": current_price,
                "change": change,
                "change_rate": change_rate,
                "change_sign": change_sign,
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                
                # 호가 정보
                "best_ask_price": best_ask,
                "best_bid_price": best_bid,
                
                # 거래량 정보
                "total_volume": total_volume,
                "total_amount": total_amount,
                "volume_ratio": volume_ratio,
                "amount_change": amount_change,
                "volume_ratio_percent": volume_ratio_percent,
                "turnover_rate": turnover_rate,
                "trading_cost": trading_cost,
                "market_cap": market_cap,
                
                # 시간 정보
                "upper_limit_time": upper_limit_time,
                "lower_limit_time": lower_limit_time,
                
                # 전체 데이터
                "raw_data": data.values,
                "readable_data": get_readable_data(data.values),
                "field_count": len(data.values)
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 향상된 로깅
            sign_desc = self._get_change_sign_description(change_sign)
            
            print(f"📋 주식기세 ({symbol}): {current_price}원 {sign_desc}{change}({change_rate}%) "
                  f"누적={total_volume} 시총={market_cap}억 필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 주식기세 처리 오류: {e}")
            return None
    
    def _get_change_sign_description(self, change_sign: str) -> str:
        """전일대비기호를 설명으로 변환"""
        if not change_sign:
            return ""
        
        # 키움 전일대비기호 매핑
        sign_map = {
            "1": "↑",  # 상승
            "2": "↓",  # 하락
            "3": "→",  # 보합
            "4": "↑",  # 상한가
            "5": "↓",  # 하한가
        }
        return sign_map.get(change_sign, change_sign)


class StockPriorityQuoteHandler(BaseRealtimeHandler):
    """0C: 주식우선호가 핸들러"""
    
    def __init__(self):
        super().__init__("0C")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식우선호가 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item
            symbol_name = data.get_field_value("302")
            
            # 호가 정보 (0C 타입의 핵심 데이터)
            best_ask = data.get_field_value("27")
            best_bid = data.get_field_value("28")
            
            # 처리된 데이터 구성
            processed_data = {
                "type": "stock_expected_price",
                "symbol": symbol,
                "symbol_name": symbol_name,
                
                # 호가 정보 (예상체결가의 핵심)
                "best_ask_price": best_ask,
                "best_bid_price": best_bid,
                
                # 전체 데이터
                "raw_data": data.values,
                "readable_data": get_readable_data(data.values),
                "field_count": len(data.values)
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간단한 로깅 (호가 정보 중심)
            print(f"📋 주식우선호가 ({symbol}): 매도호가={best_ask}원, 매수호가={best_bid}원 "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 주식우선호가 처리 오류: {e}")
            return None


class StockQuoteVolumeHandler(BaseRealtimeHandler):
    """0D: 주식호가잔량 핸들러"""
    
    def __init__(self):
        super().__init__("0D")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식ETF_NAV 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item
            symbol_name = data.get_field_value("302")
            
            # 시간 정보
            quote_time = data.get_field_value("21")
            
            # 주요 호가 정보 (1~3순위만 표시)
            ask_price_1 = data.get_field_value("41")
            ask_qty_1 = data.get_field_value("61")
            bid_price_1 = data.get_field_value("51")
            bid_qty_1 = data.get_field_value("71")
            
            # 예상체결 정보
            expected_price = data.get_field_value("23")
            expected_qty = data.get_field_value("24")
            expected_price_valid = data.get_field_value("291")  # 시간동안만 유효
            
            # 총잔량 정보
            total_ask_qty = data.get_field_value("121")
            total_bid_qty = data.get_field_value("125")
            
            # 비율 정보
            buy_ratio = data.get_field_value("129")
            sell_ratio = data.get_field_value("139")
            
            # 누적거래량
            volume = data.get_field_value("13")
            
            # 장운영구분
            market_status = data.get_field_value("215")
            
            # 처리된 데이터 구성
            processed_data = {
                "type": "stock_etf_nav",
                "symbol": symbol,
                "symbol_name": symbol_name,
                
                # 시간 정보
                "quote_time": quote_time,
                
                # 주요 호가 정보 (1순위만)
                "ask_price_1": ask_price_1,
                "ask_quantity_1": ask_qty_1,
                "bid_price_1": bid_price_1,
                "bid_quantity_1": bid_qty_1,
                
                # 예상체결 정보
                "expected_price": expected_price,
                "expected_quantity": expected_qty,
                "expected_price_valid": expected_price_valid,
                
                # 총잔량 정보
                "total_ask_quantity": total_ask_qty,
                "total_bid_quantity": total_bid_qty,
                
                # 비율 정보
                "buy_ratio": buy_ratio,
                "sell_ratio": sell_ratio,
                
                # 거래량 정보
                "volume": volume,
                "market_status": market_status,
                
                # 전체 데이터
                "raw_data": data.values,
                "readable_data": get_readable_data(data.values),
                "field_count": len(data.values)
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (주요 정보만)
            print(f"📊 주식호가잔량 ({symbol}): 예상체결={expected_price}원({expected_qty}) "
                  f"매도={ask_price_1}({ask_qty_1}) 매수={bid_price_1}({bid_qty_1}) "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 주식호가잔량 처리 오류: {e}")
            return None


class StockAfterHoursQuoteHandler(BaseRealtimeHandler):
    """0E: 주식시간외호가 핸들러"""
    
    def __init__(self):
        super().__init__("0E")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식시간외호가 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item
            symbol_name = data.get_field_value("302")  # 종목명 (있을 경우)
            
            # 시간외 호가 정보
            quote_time = data.get_field_value("21")  # 호가시간
            
            # 매도 정보 
            ask_total_qty = data.get_field_value("131")  # 시간외매도호가총잔량
            ask_total_change = data.get_field_value("132")  # 시간외매도호가총잔량직전대비
            
            # 매수 정보
            bid_total_qty = data.get_field_value("135")  # 시간외매수호가총잔량  
            bid_total_change = data.get_field_value("136")  # 시간외매수호가총잔량직전대비
            
            # 데이터 정리
            processed_data = {
                "symbol": symbol,
                "symbol_name": symbol_name,
                "quote_time": quote_time,
                "after_hours_quote": {
                    "ask_total_qty": ask_total_qty,
                    "ask_total_change": ask_total_change,
                    "bid_total_qty": bid_total_qty,
                    "bid_total_change": bid_total_change,
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (시간외 호가 정보)
            print(f"🌙 주식시간외호가 ({symbol}): 시간={quote_time} "
                  f"매도총={ask_total_qty}({ask_total_change}) 매수총={bid_total_qty}({bid_total_change}) "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 주식시간외호가 처리 오류: {e}")
            return None


class StockTradingParticipantHandler(BaseRealtimeHandler):
    """0F: 주식당일거래원 핸들러"""
    
    def __init__(self):
        super().__init__("0F")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식당일거래원 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item
            symbol_name = data.get_field_value("302")  # 종목명 (있을 경우)
            exchange_code = data.get_field_value("337")  # 거래소구분
            
            # 거래원 정보 구조화 (상위 5개)
            selling_participants = []
            buying_participants = []
            
            # 매도거래원 1~5 수집
            for i in range(1, 6):
                selling_participants.append({
                    "rank": i,
                    "name": data.get_field_value(f"{140+i}"),  # 141~145: 매도거래원명
                    "quantity": data.get_field_value(f"{160+i}"),  # 161~165: 매도거래원수량
                    "change": data.get_field_value(f"{165+i}"),  # 166~170: 매도거래원별증감
                    "code": data.get_field_value(f"{145+i}"),  # 146~150: 매도거래원코드
                    "color": data.get_field_value(f"{270+i}"),  # 271~275: 매도거래원색깔
                })
            
            # 매수거래원 1~5 수집
            for i in range(1, 6):
                buying_participants.append({
                    "rank": i,
                    "name": data.get_field_value(f"{150+i}"),  # 151~155: 매수거래원명
                    "quantity": data.get_field_value(f"{170+i}"),  # 171~175: 매수거래원수량
                    "change": data.get_field_value(f"{175+i}"),  # 176~180: 매수거래원별증감
                    "code": data.get_field_value(f"{155+i}"),  # 156~160: 매수거래원코드
                    "color": data.get_field_value(f"{280+i}"),  # 281~285: 매수거래원색깔
                })
            
            # 외국계 정보
            foreign_info = {
                "sell_estimated": data.get_field_value("261"),  # 외국계매도추정합
                "sell_change": data.get_field_value("262"),     # 외국계매도추정합변동
                "buy_estimated": data.get_field_value("263"),   # 외국계매수추정합
                "buy_change": data.get_field_value("264"),      # 외국계매수추정합변동
                "net_buy_estimated": data.get_field_value("267"),  # 외국계순매수추정합
                "net_buy_change": data.get_field_value("268"),     # 외국계순매수변동
            }
            
            # 데이터 정리
            processed_data = {
                "symbol": symbol,
                "symbol_name": symbol_name,
                "exchange_code": exchange_code,
                "selling_participants": selling_participants,
                "buying_participants": buying_participants,
                "foreign_info": foreign_info,
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (주요 거래원 정보)
            top_seller = selling_participants[0] if selling_participants[0]["name"] else "정보없음"
            top_buyer = buying_participants[0] if buying_participants[0]["name"] else "정보없음"
            
            sell_name = top_seller if isinstance(top_seller, str) else (top_seller.get("name", "정보없음") if top_seller else "정보없음")
            buy_name = top_buyer if isinstance(top_buyer, str) else (top_buyer.get("name", "정보없음") if top_buyer else "정보없음")
            
            print(f"💼 주식당일거래원 ({symbol}): "
                  f"매도1위={sell_name}({selling_participants[0]['quantity']}) "
                  f"매수1위={buy_name}({buying_participants[0]['quantity']}) "
                  f"외국계순매수={foreign_info['net_buy_estimated']} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 주식당일거래원 처리 오류: {e}")
            return None


class ETFNAVHandler(BaseRealtimeHandler):
    """0G: ETF NAV 핸들러"""
    
    def __init__(self):
        super().__init__("0G")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """ETF NAV 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item
            symbol_name = data.get_field_value("302")  # 종목명 (있을 경우)
            
            # NAV 정보
            nav = data.get_field_value("36")  # NAV
            nav_change = data.get_field_value("37")  # NAV전일대비
            nav_change_rate = data.get_field_value("38")  # NAV등락율
            tracking_error = data.get_field_value("39")  # 추적오차율
            
            # 기본 체결 정보
            execution_time = data.get_field_value("20")  # 체결시간
            current_price = data.get_field_value("10")  # 현재가
            price_change = data.get_field_value("11")  # 전일대비
            change_rate = data.get_field_value("12")  # 등락율
            volume = data.get_field_value("13")  # 누적거래량
            change_sign = data.get_field_value("25")  # 전일대비기호
            
            # 괴리율 정보
            nav_index_deviation = data.get_field_value("265")  # NAV/지수괴리율
            nav_etf_deviation = data.get_field_value("266")  # NAV/ETF괴리율
            
            # ELW 관련 (선택적)
            elw_gearing = data.get_field_value("667")  # ELW기어링비율
            elw_breakeven = data.get_field_value("668")  # ELW손익분기율
            elw_support = data.get_field_value("669")  # ELW자본지지점
            
            # 데이터 정리
            processed_data = {
                "symbol": symbol,
                "symbol_name": symbol_name,
                "nav_info": {
                    "nav": nav,
                    "nav_change": nav_change,
                    "nav_change_rate": nav_change_rate,
                    "tracking_error": tracking_error,
                },
                "price_info": {
                    "execution_time": execution_time,
                    "current_price": current_price,
                    "price_change": price_change,
                    "change_rate": change_rate,
                    "volume": volume,
                    "change_sign": change_sign,
                },
                "deviation_info": {
                    "nav_index_deviation": nav_index_deviation,
                    "nav_etf_deviation": nav_etf_deviation,
                },
                "elw_info": {
                    "gearing": elw_gearing,
                    "breakeven": elw_breakeven,
                    "support": elw_support,
                } if any([elw_gearing, elw_breakeven, elw_support]) else None,
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 전일대비기호 설명
            sign_desc = self._get_change_sign_description(change_sign)
            
            # 간결한 로깅 (ETF NAV 정보 중심)
            print(f"📈 ETF NAV ({symbol}): NAV={nav}({nav_change}/{nav_change_rate}%) "
                  f"현재가={current_price}원({sign_desc}{price_change}/{change_rate}%) "
                  f"추적오차={tracking_error}% 지수괴리={nav_index_deviation}% "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ ETF NAV 처리 오류: {e}")
            return None
    
    def _get_change_sign_description(self, change_sign: str) -> str:
        """전일대비기호를 설명으로 변환"""
        sign_map = {
            "1": "상한",
            "2": "상승",
            "3": "보합",
            "4": "하한",
            "5": "하락",
        }
        return sign_map.get(change_sign, change_sign)


class StockExpectedExecutionHandler(BaseRealtimeHandler):
    """0H: 주식예상체결 핸들러"""
    
    def __init__(self):
        super().__init__("0H")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식예상체결 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item
            symbol_name = data.get_field_value("302")  # 종목명 (있을 경우)
            
            # 체결 정보
            execution_time = data.get_field_value("20")  # 체결시간
            current_price = data.get_field_value("10")  # 현재가
            price_change = data.get_field_value("11")  # 전일대비
            change_rate = data.get_field_value("12")  # 등락율
            volume = data.get_field_value("15")  # 거래량 (+는 매수체결, -는 매도체결)
            total_volume = data.get_field_value("13")  # 누적거래량
            change_sign = data.get_field_value("25")  # 전일대비기호
            
            # 매수/매도 구분 (거래량 부호로 판단)
            trade_type = None
            if volume:
                if volume.startswith('+'):
                    trade_type = "매수체결"
                    volume_abs = volume[1:]  # '+' 제거
                elif volume.startswith('-'):
                    trade_type = "매도체결"
                    volume_abs = volume[1:]  # '-' 제거
                else:
                    trade_type = "알 수 없음"
                    volume_abs = volume
            else:
                volume_abs = "0"
                trade_type = "정보없음"
            
            # 데이터 정리
            processed_data = {
                "symbol": symbol,
                "symbol_name": symbol_name,
                "execution_info": {
                    "execution_time": execution_time,
                    "current_price": current_price,
                    "price_change": price_change,
                    "change_rate": change_rate,
                    "change_sign": change_sign,
                },
                "volume_info": {
                    "volume": volume_abs,
                    "trade_type": trade_type,
                    "total_volume": total_volume,
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 전일대비기호 설명
            sign_desc = self._get_change_sign_description(change_sign)
            
            # 간결한 로깅 (예상체결 정보)
            print(f"🎯 주식예상체결 ({symbol}): {execution_time} "
                  f"{current_price}원({sign_desc}{price_change}/{change_rate}%) "
                  f"{trade_type}={volume_abs} 누적={total_volume} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 주식예상체결 처리 오류: {e}")
            return None
    
    def _get_change_sign_description(self, change_sign: str) -> str:
        """전일대비기호를 설명으로 변환"""
        sign_map = {
            "1": "상한",
            "2": "상승",
            "3": "보합",
            "4": "하한",
            "5": "하락",
        }
        return sign_map.get(change_sign, change_sign)


class SectorIndexHandler(BaseRealtimeHandler):
    """0J: 업종지수 핸들러"""
    
    def __init__(self):
        super().__init__("0J")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """업종지수 데이터 처리"""
        try:
            # 기본 정보
            sector_code = data.item  # 업종코드 (예: 001)
            sector_name = data.get_field_value("302")  # 업종명 (있을 경우)
            
            # 지수 정보
            execution_time = data.get_field_value("20")  # 체결시간
            current_index = data.get_field_value("10")  # 현재 지수값
            index_change = data.get_field_value("11")  # 전일대비
            change_rate = data.get_field_value("12")  # 등락율
            change_sign = data.get_field_value("25")  # 전일대비기호
            
            # 거래량 정보
            volume = data.get_field_value("15")  # 거래량 (+는 매수체결, -는 매도체결)
            total_volume = data.get_field_value("13")  # 누적거래량
            total_amount = data.get_field_value("14")  # 누적거래대금
            volume_change = data.get_field_value("26")  # 전일거래량대비
            
            # OHLC 정보
            open_index = data.get_field_value("16")  # 시가
            high_index = data.get_field_value("17")  # 고가
            low_index = data.get_field_value("18")  # 저가
            
            # 업종코드 해석 (일반적인 업종코드)
            sector_info = self._get_sector_name(sector_code)
            
            # 데이터 정리
            processed_data = {
                "sector_code": sector_code,
                "sector_name": sector_name or sector_info,
                "index_info": {
                    "execution_time": execution_time,
                    "current_index": current_index,
                    "index_change": index_change,
                    "change_rate": change_rate,
                    "change_sign": change_sign,
                    "open_index": open_index,
                    "high_index": high_index,
                    "low_index": low_index,
                },
                "trading_info": {
                    "volume": volume,
                    "total_volume": total_volume,
                    "total_amount": total_amount,
                    "volume_change": volume_change,
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 전일대비기호 설명
            sign_desc = self._get_change_sign_description(change_sign)
            
            # 간결한 로깅 (업종지수 정보)
            print(f"📊 업종지수 ({sector_code}-{sector_info}): {execution_time} "
                  f"지수={current_index}({sign_desc}{index_change}/{change_rate}%) "
                  f"고={high_index} 저={low_index} 거래량={total_volume} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 업종지수 처리 오류: {e}")
            return None
    
    def _get_change_sign_description(self, change_sign: str) -> str:
        """전일대비기호를 설명으로 변환"""
        sign_map = {
            "1": "상한",
            "2": "상승",
            "3": "보합",
            "4": "하한",
            "5": "하락",
        }
        return sign_map.get(change_sign, change_sign)
    
    def _get_sector_name(self, sector_code: str) -> str:
        """업종코드를 업종명으로 변환"""
        sector_map = {
            "001": "종합주가지수",
            "002": "대형주",
            "003": "중형주", 
            "004": "소형주",
            "101": "음식료업",
            "102": "섬유의복",
            "103": "종이목재",
            "104": "화학",
            "105": "의약품",
            "106": "비금속광물",
            "107": "철강금속",
            "108": "기계",
            "109": "전기전자",
            "110": "의료정밀",
            "111": "운수장비",
            "112": "유통업",
            "113": "전기가스업",
            "114": "건설업",
            "115": "운수창고업",
            "116": "통신업",
            "117": "금융업",
            "118": "은행",
            "119": "증권",
            "120": "보험",
            "121": "서비스업",
            "122": "제조업",
        }
        return sector_map.get(sector_code, f"업종({sector_code})")


class SectorFluctuationHandler(BaseRealtimeHandler):
    """0U: 업종등락 핸들러"""
    
    def __init__(self):
        super().__init__("0U")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """업종등락 데이터 처리"""
        try:
            # 기본 정보
            sector_code = data.item  # 업종코드 (예: 001)
            sector_name = data.get_field_value("302")  # 업종명 (있을 경우)
            
            # 시간 및 지수 정보
            execution_time = data.get_field_value("20")  # 체결시간
            current_index = data.get_field_value("10")  # 현재 지수값
            index_change = data.get_field_value("11")  # 전일대비
            change_rate = data.get_field_value("12")  # 등락율
            change_sign = data.get_field_value("25")  # 전일대비기호
            
            # 종목 등락 정보
            up_limit_count = data.get_field_value("251")  # 상한종목수
            up_count = data.get_field_value("252")  # 상승종목수
            unchanged_count = data.get_field_value("253")  # 보합종목수
            down_limit_count = data.get_field_value("254")  # 하한종목수
            down_count = data.get_field_value("255")  # 하락종목수
            
            # 거래 정보
            total_volume = data.get_field_value("13")  # 누적거래량
            total_amount = data.get_field_value("14")  # 누적거래대금
            trading_stocks = data.get_field_value("256")  # 거래형성종목수
            trading_ratio = data.get_field_value("257")  # 거래형성비율
            
            # 업종코드 해석 (0J에서 사용한 매핑 재사용)
            sector_info = self._get_sector_name(sector_code)
            
            # 총 종목수 계산 (상한+상승+보합+하한+하락)
            total_stocks = 0
            for count_str in [up_limit_count, up_count, unchanged_count, down_limit_count, down_count]:
                if count_str and count_str.isdigit():
                    total_stocks += int(count_str)
            
            # 데이터 정리
            processed_data = {
                "sector_code": sector_code,
                "sector_name": sector_name or sector_info,
                "index_info": {
                    "execution_time": execution_time,
                    "current_index": current_index,
                    "index_change": index_change,
                    "change_rate": change_rate,
                    "change_sign": change_sign,
                },
                "fluctuation_info": {
                    "up_limit_count": up_limit_count,
                    "up_count": up_count,
                    "unchanged_count": unchanged_count,
                    "down_count": down_count,
                    "down_limit_count": down_limit_count,
                    "total_stocks": str(total_stocks) if total_stocks > 0 else "0",
                },
                "trading_info": {
                    "total_volume": total_volume,
                    "total_amount": total_amount,
                    "trading_stocks": trading_stocks,
                    "trading_ratio": trading_ratio,
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 전일대비기호 설명
            sign_desc = self._get_change_sign_description(change_sign)
            
            # 간결한 로깅 (업종등락 정보)
            print(f"📈 업종등락 ({sector_code}-{sector_info}): {execution_time} "
                  f"지수={current_index}({sign_desc}{index_change}/{change_rate}%) "
                  f"상승={up_count} 하락={down_count} 보합={unchanged_count} "
                  f"거래형성={trading_stocks}({trading_ratio}%) "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 업종등락 처리 오류: {e}")
            return None
    
    def _get_change_sign_description(self, change_sign: str) -> str:
        """전일대비기호를 설명으로 변환"""
        sign_map = {
            "1": "상한",
            "2": "상승",
            "3": "보합",
            "4": "하한",
            "5": "하락",
        }
        return sign_map.get(change_sign, change_sign)
    
    def _get_sector_name(self, sector_code: str) -> str:
        """업종코드를 업종명으로 변환 (0J와 동일한 매핑)"""
        sector_map = {
            "001": "종합주가지수",
            "002": "대형주",
            "003": "중형주", 
            "004": "소형주",
            "101": "음식료업",
            "102": "섬유의복",
            "103": "종이목재",
            "104": "화학",
            "105": "의약품",
            "106": "비금속광물",
            "107": "철강금속",
            "108": "기계",
            "109": "전기전자",
            "110": "의료정밀",
            "111": "운수장비",
            "112": "유통업",
            "113": "전기가스업",
            "114": "건설업",
            "115": "운수창고업",
            "116": "통신업",
            "117": "금융업",
            "118": "은행",
            "119": "증권",
            "120": "보험",
            "121": "서비스업",
            "122": "제조업",
        }
        return sector_map.get(sector_code, f"업종({sector_code})")


class StockSymbolInfoHandler(BaseRealtimeHandler):
    """0g: 주식종목정보 핸들러"""
    
    def __init__(self):
        super().__init__("0g")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """주식종목정보 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item  # 종목코드
            
            # 가격 정보
            upper_limit = data.get_field_value("305")  # 상한가
            lower_limit = data.get_field_value("306")  # 하한가
            base_price = data.get_field_value("307")   # 기준가
            
            # 연장 관련 정보
            arbitrary_extension = data.get_field_value("297")      # 임의연장
            pre_market_extension = data.get_field_value("592")     # 장전임의연장
            after_market_extension = data.get_field_value("593")   # 장후임의연장
            
            # 기타 정보
            early_termination_elw = data.get_field_value("689")    # 조기종료ELW발생
            currency_unit = data.get_field_value("594")            # 통화단위
            margin_rate_display = data.get_field_value("382")      # 증거금율표시
            symbol_info = data.get_field_value("370")              # 종목정보
            
            # 가격 정보 숫자 변환 (+ 접두사 제거)
            def parse_price(price_str: str) -> Optional[str]:
                if not price_str or price_str.strip() == '':
                    return None
                # + 접두사 제거
                clean_price = price_str.lstrip('+')
                return clean_price
            
            # 연장 정보 해석
            def get_extension_description(ext_code: str) -> str:
                """연장 코드를 설명으로 변환"""
                ext_map = {
                    "동정적VI": "동적 변동성 중단",
                    "정적VI": "정적 변동성 중단", 
                    "": "정상",
                    " ": "정상"
                }
                return ext_map.get(ext_code, ext_code if ext_code else "정상")
            
            # 데이터 정리
            processed_data = {
                "symbol": symbol,
                "price_info": {
                    "upper_limit": parse_price(upper_limit),
                    "lower_limit": parse_price(lower_limit), 
                    "base_price": parse_price(base_price),
                },
                "extension_info": {
                    "arbitrary_extension": arbitrary_extension,
                    "arbitrary_extension_desc": get_extension_description(arbitrary_extension),
                    "pre_market_extension": pre_market_extension,
                    "after_market_extension": after_market_extension,
                },
                "additional_info": {
                    "early_termination_elw": early_termination_elw,
                    "currency_unit": currency_unit,
                    "margin_rate_display": margin_rate_display,
                    "symbol_info": symbol_info,
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (종목정보)
            ext_desc = get_extension_description(arbitrary_extension)
            print(f"📋 종목정보 ({symbol}): "
                  f"기준가={base_price} 상한={upper_limit} 하한={lower_limit} "
                  f"연장상태={ext_desc} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 종목정보 처리 오류: {e}")
            return None


class ELWTheoreticalPriceHandler(BaseRealtimeHandler):
    """0m: ELW 이론가 핸들러"""
    
    def __init__(self):
        super().__init__("0m")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """ELW 이론가 데이터 처리"""
        try:
            # 기본 정보
            elw_code = data.item  # ELW 종목코드
            execution_time = data.get_field_value("20")  # 체결시간
            current_price = data.get_field_value("10")   # 현재가
            
            # ELW 이론가 정보
            theoretical_price = data.get_field_value("670")  # ELW이론가
            implied_volatility = data.get_field_value("671") # ELW내재변동성
            lp_implied_volatility = data.get_field_value("706") # LP호가내재변동성
            
            # Greeks 정보
            delta = data.get_field_value("672")  # ELW델타 (가격민감도)
            gamma = data.get_field_value("673")  # ELW감마 (델타변화율)
            theta = data.get_field_value("674")  # ELW쎄타 (시간가치감소)
            vega = data.get_field_value("675")   # ELW베가 (변동성민감도)
            rho = data.get_field_value("676")    # ELW로 (금리민감도)
            
            # 숫자 데이터 정리 함수
            def parse_float(value_str: str) -> Optional[float]:
                """문자열을 float로 안전하게 변환"""
                if not value_str or value_str.strip() == '' or value_str.strip() == '0':
                    return None
                try:
                    # 공백 제거 후 변환
                    clean_value = value_str.strip()
                    return float(clean_value) if clean_value != '0' else 0.0
                except (ValueError, TypeError):
                    return None
            
            def parse_int(value_str: str) -> Optional[int]:
                """문자열을 int로 안전하게 변환"""
                if not value_str or value_str.strip() == '' or value_str.strip() == '0':
                    return None
                try:
                    clean_value = value_str.strip()
                    return int(clean_value) if clean_value != '0' else 0
                except (ValueError, TypeError):
                    return None
            
            # 데이터 정리
            processed_data = {
                "elw_code": elw_code,
                "execution_time": execution_time,
                "price_info": {
                    "current_price": parse_int(current_price),
                    "theoretical_price": parse_int(theoretical_price),
                },
                "volatility_info": {
                    "implied_volatility": parse_float(implied_volatility),
                    "lp_implied_volatility": parse_float(lp_implied_volatility),
                },
                "greeks": {
                    "delta": parse_float(delta),      # 기초자산 가격 변화에 대한 민감도
                    "gamma": parse_float(gamma),      # 델타의 변화율
                    "theta": parse_float(theta),      # 시간 경과에 따른 가치 감소
                    "vega": parse_float(vega),        # 변동성 변화에 대한 민감도
                    "rho": parse_float(rho),          # 금리 변화에 대한 민감도
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (ELW 정보)
            iv_str = f"{implied_volatility}%" if implied_volatility and implied_volatility.strip() != '0.00' else "N/A"
            delta_str = delta if delta and delta.strip() != '0' else "N/A"
            
            print(f"📊 ELW이론가 ({elw_code}): {execution_time} "
                  f"현재가={current_price} 이론가={theoretical_price} "
                  f"IV={iv_str} 델타={delta_str} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ ELW 이론가 처리 오류: {e}")
            return None


class MarketOpenTimeHandler(BaseRealtimeHandler):
    """0s: 장시작시간 핸들러"""
    
    def __init__(self):
        super().__init__("0s")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """장시작시간 데이터 처리"""
        try:
            # 기본 정보 (item은 빈 문자열)
            execution_time = data.get_field_value("20")  # 체결시간
            market_status = data.get_field_value("215")  # 장운영구분
            time_to_open = data.get_field_value("214")   # 장시작예상잔여시간
            
            # 장운영구분 해석
            def get_market_status_description(status_code: str) -> str:
                """장운영구분 코드를 설명으로 변환"""
                status_map = {
                    "0": "KRX장전",
                    "3": "KRX장시작", 
                    "P": "NXT프리마켓개시",
                    "Q": "NXT프리마켓종료",
                    "R": "NXT메인마켓개시",
                    "S": "NXT메인마켓종료",
                    "T": "NXT애프터마켓단일가개시", 
                    "U": "NXT애프터마켓개시",
                    "V": "NXT종가매매종료",
                    "W": "NXT애프터마켓종료",
                    "b": "시장전체휴장",  # 실제 예시에서 'b' 값이 나타남
                }
                return status_map.get(status_code, f"알수없음({status_code})")
            
            # 시간 포맷팅
            def format_time(time_str: str) -> str:
                """HHMMSS 형식의 시간을 HH:MM:SS로 변환"""
                if not time_str or len(time_str) < 6:
                    return time_str
                return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            
            def format_remaining_time(time_str: str) -> str:
                """잔여시간을 읽기 쉬운 형식으로 변환"""
                if not time_str or time_str == "000000":
                    return "해당없음"
                
                if len(time_str) >= 6:
                    hours = int(time_str[:2])
                    minutes = int(time_str[2:4])
                    seconds = int(time_str[4:6])
                    
                    if hours > 0:
                        return f"{hours}시간 {minutes}분 {seconds}초"
                    elif minutes > 0:
                        return f"{minutes}분 {seconds}초"
                    else:
                        return f"{seconds}초"
                
                return time_str
            
            # 시장 상태 분류
            def get_market_category(status_code: str) -> str:
                """시장 상태를 카테고리로 분류"""
                if status_code in ["0"]:
                    return "장전"
                elif status_code in ["3"]:
                    return "정규장"
                elif status_code in ["P", "R", "U"]:
                    return "개시"
                elif status_code in ["Q", "S", "V", "W"]:
                    return "종료"
                elif status_code in ["T"]:
                    return "단일가"
                elif status_code in ["b"]:
                    return "휴장"
                else:
                    return "기타"
            
            # 데이터 정리
            status_description = get_market_status_description(market_status)
            market_category = get_market_category(market_status)
            formatted_time = format_time(execution_time)
            formatted_remaining = format_remaining_time(time_to_open)
            
            processed_data = {
                "execution_time": execution_time,
                "formatted_time": formatted_time,
                "market_info": {
                    "status_code": market_status,
                    "status_description": status_description,
                    "market_category": market_category,
                    "time_to_open": time_to_open,
                    "formatted_remaining_time": formatted_remaining,
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (시장 상태)
            print(f"🕐 장시작시간: {formatted_time} "
                  f"상태={status_description}({market_category}) "
                  f"잔여={formatted_remaining} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 장시작시간 처리 오류: {e}")
            return None


class ELWIndicatorHandler(BaseRealtimeHandler):
    """0u: ELW 지표 핸들러"""
    
    def __init__(self):
        super().__init__("0u")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """ELW 지표 데이터 처리"""
        try:
            # 기본 정보
            elw_code = data.item  # ELW 종목코드
            execution_time = data.get_field_value("20")  # 체결시간
            
            # ELW 지표 정보
            parity = data.get_field_value("666")          # ELW패리티
            premium = data.get_field_value("1211")        # ELW프리미엄
            gearing_ratio = data.get_field_value("667")   # ELW기어링비율
            breakeven_rate = data.get_field_value("668")  # ELW손익분기율
            capital_support = data.get_field_value("669") # ELW자본지지점
            
            # 숫자 데이터 정리 함수
            def parse_float_with_sign(value_str: str) -> Optional[float]:
                """+ 또는 - 부호가 있는 문자열을 float로 변환"""
                if not value_str or value_str.strip() == '' or value_str.strip() == '0':
                    return None
                try:
                    # +/- 부호 처리
                    clean_value = value_str.strip()
                    return float(clean_value)
                except (ValueError, TypeError):
                    return None
            
            def parse_float(value_str: str) -> Optional[float]:
                """문자열을 float로 안전하게 변환"""
                if not value_str or value_str.strip() == '' or value_str.strip() == '0':
                    return None
                try:
                    clean_value = value_str.strip()
                    return float(clean_value) if clean_value != '0' else 0.0
                except (ValueError, TypeError):
                    return None
            
            # 시간 포맷팅
            def format_time(time_str: str) -> str:
                """HHMMSS 형식의 시간을 HH:MM:SS로 변환"""
                if not time_str or len(time_str) < 6:
                    return time_str
                return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            
            # 패리티 해석
            def interpret_parity(parity_val: Optional[float]) -> str:
                """패리티 값 해석"""
                if parity_val is None:
                    return "N/A"
                if parity_val > 0:
                    return f"기초자산대비 {parity_val:.2f}% 높음"
                elif parity_val < 0:
                    return f"기초자산대비 {abs(parity_val):.2f}% 낮음"
                else:
                    return "기초자산과 동일"
            
            # 기어링 해석
            def interpret_gearing(gearing_val: Optional[float]) -> str:
                """기어링 비율 해석"""
                if gearing_val is None:
                    return "N/A"
                if gearing_val > 10:
                    return f"고기어링 ({gearing_val:.2f}배)"
                elif gearing_val > 5:
                    return f"중기어링 ({gearing_val:.2f}배)"
                else:
                    return f"저기어링 ({gearing_val:.2f}배)"
            
            # 데이터 정리
            parity_val = parse_float(parity)
            premium_val = parse_float(premium) 
            gearing_val = parse_float(gearing_ratio)
            breakeven_val = parse_float_with_sign(breakeven_rate)
            capital_val = parse_float_with_sign(capital_support)
            
            processed_data = {
                "elw_code": elw_code,
                "execution_time": execution_time,
                "formatted_time": format_time(execution_time),
                "indicators": {
                    "parity": parity_val,                    # 패리티 (기초자산 대비 비율)
                    "parity_interpretation": interpret_parity(parity_val),
                    "premium": premium_val,                  # 프리미엄 (시간가치)
                    "gearing_ratio": gearing_val,            # 기어링 비율 (레버리지)
                    "gearing_interpretation": interpret_gearing(gearing_val),
                    "breakeven_rate": breakeven_val,         # 손익분기율
                    "capital_support": capital_val,          # 자본지지점
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (ELW 지표)
            parity_str = f"{parity}%" if parity and parity.strip() != '0' else "N/A"
            gearing_str = f"{gearing_ratio}배" if gearing_ratio and gearing_ratio.strip() != '0' else "N/A"
            premium_str = premium if premium and premium.strip() != '0' else "N/A"
            
            print(f"📊 ELW지표 ({elw_code}): {format_time(execution_time)} "
                  f"패리티={parity_str} 기어링={gearing_str} "
                  f"프리미엄={premium_str} 손익분기={breakeven_rate} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ ELW 지표 처리 오류: {e}")
            return None


class DefaultHandler(BaseRealtimeHandler):
    """기본 핸들러 (지원하지 않는 타입용)"""
    
    def __init__(self, type_code: str):
        super().__init__(type_code)
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """기본 데이터 처리"""
        try:
            # 기본 처리
            processed_data = {
                "type": f"unknown_{self.type_code}",
                "symbol": data.item,
                "raw_data": data.values,
                "readable_data": get_readable_data(data.values)
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            print(f"📋 타입 {self.type_code} ({data.item}): {len(data.values)}개 필드")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 기본 핸들러 처리 오류: {e}")
            return None


class TypeHandlerRegistry:
    """타입별 핸들러 레지스트리"""
    
    def __init__(self):
        self._handlers: Dict[str, BaseRealtimeHandler] = {}
        self._initialize_default_handlers()
        
    def _initialize_default_handlers(self):
        """기본 핸들러들 초기화"""
        self.register_handler("00", StockQuoteHandler())
        self.register_handler("04", BalanceHandler())
        self.register_handler("0A", StockMomentumHandler())
        self.register_handler("0B", StockExecutionHandler())
        self.register_handler("0C", StockPriorityQuoteHandler())
        self.register_handler("0D", StockQuoteVolumeHandler())
        self.register_handler("0E", StockAfterHoursQuoteHandler())
        self.register_handler("0F", StockTradingParticipantHandler())
        self.register_handler("0G", ETFNAVHandler())
        self.register_handler("0H", StockExpectedExecutionHandler())
        self.register_handler("0J", SectorIndexHandler())
        self.register_handler("0U", SectorFluctuationHandler())
        self.register_handler("0g", StockSymbolInfoHandler())
        self.register_handler("0m", ELWTheoreticalPriceHandler())
        self.register_handler("0s", MarketOpenTimeHandler())
        self.register_handler("0u", ELWIndicatorHandler())
        self.register_handler("0w", ProgramTradingHandler())
        self.register_handler("1h", VIHandler())
        
    def register_handler(self, type_code: str, handler: BaseRealtimeHandler) -> None:
        """핸들러 등록"""
        self._handlers[type_code] = handler
        print(f"📋 핸들러 등록: {type_code} -> {handler.__class__.__name__}")
        
    def get_handler(self, type_code: str) -> BaseRealtimeHandler:
        """핸들러 조회 (없으면 기본 핸들러 반환)"""
        if type_code in self._handlers:
            return self._handlers[type_code]
        else:
            # 지원하지 않는 타입은 기본 핸들러 생성
            default_handler = DefaultHandler(type_code)
            self._handlers[type_code] = default_handler
            return default_handler
            
    def has_handler(self, type_code: str) -> bool:
        """핸들러 존재 여부 확인"""
        return type_code in self._handlers
        
    def get_supported_types(self) -> list[str]:
        """지원하는 타입 목록 반환"""
        return list(self._handlers.keys())
        
    async def handle_data(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """데이터를 적절한 핸들러로 라우팅"""
        handler = self.get_handler(data.type)
        return await handler.handle(data)

class ProgramTradingHandler(BaseRealtimeHandler):
    """0w: 종목프로그램매매 핸들러"""
    
    def __init__(self):
        super().__init__("0w")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """종목프로그램매매 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.item  # 종목코드
            execution_time = data.get_field_value("20")  # 체결시간
            current_price = data.get_field_value("10")   # 현재가
            change_sign = data.get_field_value("25")     # 전일대비기호
            change = data.get_field_value("11")          # 전일대비
            change_rate = data.get_field_value("12")     # 등락율
            total_volume = data.get_field_value("13")    # 누적거래량
            
            # 프로그램매매 정보
            sell_quantity = data.get_field_value("202")  # 매도수량
            sell_amount = data.get_field_value("204")    # 매도금액
            buy_quantity = data.get_field_value("206")   # 매수수량
            buy_amount = data.get_field_value("208")     # 매수금액
            net_buy_quantity = data.get_field_value("210")  # 순매수수량
            net_buy_qty_change = data.get_field_value("211")  # 순매수수량증감
            net_buy_amount = data.get_field_value("212")     # 순매수금액
            net_buy_amt_change = data.get_field_value("213") # 순매수금액증감
            
            # 시장 정보
            market_remaining_time = data.get_field_value("214")  # 장시작예상잔여시간
            market_status = data.get_field_value("215")          # 장운영구분
            investor_ticker = data.get_field_value("216")        # 투자자별ticker
            
            # 숫자 데이터 처리 함수
            def parse_int(value_str: str) -> int:
                """문자열을 정수로 안전하게 변환"""
                if not value_str or value_str.strip() == "" or value_str.strip() == "0":
                    return 0
                try:
                    clean_value = value_str.strip()
                    # +/- 부호 처리
                    if clean_value.startswith("+"):
                        clean_value = clean_value[1:]
                    return int(clean_value)
                except (ValueError, TypeError):
                    return 0
            
            def parse_float(value_str: str) -> Optional[float]:
                """문자열을 float로 안전하게 변환"""
                if not value_str or value_str.strip() == "":
                    return None
                try:
                    clean_value = value_str.strip()
                    if clean_value.startswith("+"):
                        clean_value = clean_value[1:]
                    return float(clean_value)
                except (ValueError, TypeError):
                    return None
            
            # 시간 포맷팅
            def format_time(time_str: str) -> str:
                """HHMMSS 형식의 시간을 HH:MM:SS로 변환"""
                if not time_str or len(time_str) < 6:
                    return time_str
                return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            
            # 프로그램매매 방향 판단
            def get_program_direction(net_qty: int, net_qty_change: int) -> Dict[str, str]:
                """프로그램매매 방향 판단"""
                direction = "중립"
                intensity = "보통"
                
                if net_qty > 0:
                    direction = "매수우위"
                    if net_qty > 10000:
                        intensity = "강세"
                    elif net_qty > 5000:
                        intensity = "보통"
                    else:
                        intensity = "약세"
                elif net_qty < 0:
                    direction = "매도우위"
                    if abs(net_qty) > 10000:
                        intensity = "강세"
                    elif abs(net_qty) > 5000:
                        intensity = "보통"
                    else:
                        intensity = "약세"
                
                return {"direction": direction, "intensity": intensity}
            
            # 시장상태 해석
            def get_market_status_desc(status: str) -> str:
                """장운영구분 해석"""
                status_map = {
                    "0": "장시작전",
                    "1": "장중",
                    "2": "장종료",
                    "3": "시간외단일가매매중", 
                    "4": "시간외단일가매매종료",
                }
                return status_map.get(status, f"알수없음({status})")
            
            # 변동기호 해석
            def get_change_sign_desc(sign: str) -> str:
                """전일대비기호 해석"""
                sign_map = {
                    "1": "상한",
                    "2": "상승",
                    "3": "보합",
                    "4": "하한",
                    "5": "하락",
                }
                return sign_map.get(sign, sign)
            
            # 데이터 변환
            parsed_sell_qty = parse_int(sell_quantity)
            parsed_buy_qty = parse_int(buy_quantity)
            parsed_net_qty = parse_int(net_buy_quantity)
            parsed_net_qty_change = parse_int(net_buy_qty_change)
            
            parsed_sell_amt = parse_float(sell_amount)
            parsed_buy_amt = parse_float(buy_amount)
            parsed_net_amt = parse_float(net_buy_amount)
            parsed_net_amt_change = parse_float(net_buy_amt_change)
            
            # 프로그램매매 방향 분석
            program_analysis = get_program_direction(parsed_net_qty, parsed_net_qty_change)
            
            # 거래 비율 계산
            total_program_qty = parsed_sell_qty + parsed_buy_qty
            buy_ratio = (parsed_buy_qty / total_program_qty * 100) if total_program_qty > 0 else 0
            sell_ratio = (parsed_sell_qty / total_program_qty * 100) if total_program_qty > 0 else 0
            
            # 데이터 정리
            processed_data = {
                "symbol": symbol,
                "execution_time": format_time(execution_time) if execution_time else None,
                "price_info": {
                    "current_price": current_price,
                    "change": change,
                    "change_rate": change_rate,
                    "change_sign": change_sign,
                    "change_sign_desc": get_change_sign_desc(change_sign),
                    "total_volume": total_volume,
                },
                "program_trading": {
                    "sell_quantity": parsed_sell_qty,
                    "sell_amount": parsed_sell_amt,
                    "buy_quantity": parsed_buy_qty,
                    "buy_amount": parsed_buy_amt,
                    "net_buy_quantity": parsed_net_qty,
                    "net_buy_quantity_change": parsed_net_qty_change,
                    "net_buy_amount": parsed_net_amt,
                    "net_buy_amount_change": parsed_net_amt_change,
                    "buy_ratio": round(buy_ratio, 2),
                    "sell_ratio": round(sell_ratio, 2),
                    "direction": program_analysis["direction"],
                    "intensity": program_analysis["intensity"],
                },
                "market_info": {
                    "remaining_time": market_remaining_time,
                    "market_status": market_status,
                    "market_status_desc": get_market_status_desc(market_status),
                    "investor_ticker": investor_ticker,
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (프로그램매매 정보)
            formatted_time = format_time(execution_time) if execution_time else execution_time
            change_desc = get_change_sign_desc(change_sign)
            market_desc = get_market_status_desc(market_status)
            
            print(f"🤖 프로그램매매 ({symbol}): {formatted_time} "
                  f"현재가={current_price}({change_desc}{change}/{change_rate}%) "
                  f"순매수={parsed_net_qty}({parsed_net_qty_change:+d}) "
                  f"매수={parsed_buy_qty} 매도={parsed_sell_qty} "
                  f"방향={program_analysis['direction']}({program_analysis['intensity']}) "
                  f"시장={market_desc} 필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ 종목프로그램매매 처리 오류: {e}")
            return None




class VIHandler(BaseRealtimeHandler):
    """1h: VI발동/해제 핸들러"""
    
    def __init__(self):
        super().__init__("1h")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """VI발동/해제 데이터 처리"""
        try:
            # 기본 정보
            symbol = data.get_field_value("9001")       # 종목코드
            symbol_name = data.get_field_value("302")   # 종목명
            total_volume = data.get_field_value("13")   # 누적거래량
            total_amount = data.get_field_value("14")   # 누적거래대금
            
            # VI 정보
            vi_trigger_type = data.get_field_value("9068")      # VI발동구분
            market_type = data.get_field_value("9008")          # KOSPI,KOSDAQ,전체구분  
            pre_market_type = data.get_field_value("9075")      # 장전구분
            vi_trigger_price = data.get_field_value("1221")     # VI발동가격
            execution_time = data.get_field_value("1223")       # 매매체결처리시각
            vi_release_time = data.get_field_value("1224")      # VI해제시각
            vi_apply_type = data.get_field_value("1225")        # VI적용구분
            
            # 기준가격 정보
            static_base_price = data.get_field_value("1236")    # 기준가격 정적
            dynamic_base_price = data.get_field_value("1237")   # 기준가격 동적
            static_deviation = data.get_field_value("1238")     # 괴리율 정적
            dynamic_deviation = data.get_field_value("1239")    # 괴리율 동적
            
            # 추가 정보
            vi_price_change_rate = data.get_field_value("1489") # VI발동가 등락율
            vi_trigger_count = data.get_field_value("1490")     # VI발동횟수
            trigger_direction = data.get_field_value("9069")    # 발동방향구분
            extra_item = data.get_field_value("1279")           # Extra Item
            
            # 해석 함수들
            def get_vi_trigger_description(trigger_type: str) -> str:
                """VI발동구분 해석"""
                trigger_map = {
                    "0": "발동없음",
                    "1": "정적VI발동",
                    "2": "동적VI발동", 
                    "3": "정적+동적VI발동",
                    "4": "VI해제",
                }
                return trigger_map.get(trigger_type, f"알수없음({trigger_type})")
            
            def get_market_description(market_code: str) -> str:
                """시장구분 해석"""
                market_map = {
                    "101": "KOSPI",
                    "201": "KOSDAQ",
                    "301": "KRX",
                    "801": "ETF",
                }
                return market_map.get(market_code, f"기타({market_code})")
            
            def get_pre_market_description(pre_market: str) -> str:
                """장전구분 해석"""
                pre_market_map = {
                    "0": "정규장",
                    "1": "장전시간외",
                    "2": "장후시간외",
                }
                return pre_market_map.get(pre_market, f"알수없음({pre_market})")
            
            def get_trigger_direction_description(direction: str) -> str:
                """발동방향구분 해석"""
                direction_map = {
                    "1": "상승방향",
                    "2": "하락방향",
                    "0": "해당없음",
                }
                return direction_map.get(direction, f"알수없음({direction})")
            
            def format_time(time_str: str) -> str:
                """HHMMSS 형식의 시간을 HH:MM:SS로 변환"""
                if not time_str or len(time_str) < 6:
                    return time_str
                return f"{time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
            
            def parse_float_with_sign(value_str: str) -> Optional[float]:
                """+ 또는 - 부호가 있는 문자열을 float로 변환"""
                if not value_str or value_str.strip() == "":
                    return None
                try:
                    clean_value = value_str.strip()
                    return float(clean_value)
                except (ValueError, TypeError):
                    return None
            
            def parse_int(value_str: str) -> Optional[int]:
                """문자열을 정수로 안전하게 변환"""
                if not value_str or value_str.strip() == "":
                    return None
                try:
                    clean_value = value_str.strip()
                    return int(clean_value)
                except (ValueError, TypeError):
                    return None
            
            # VI 상태 판단
            def get_vi_status(trigger_type: str, release_time: str) -> str:
                """VI 현재 상태 판단"""
                if trigger_type in ["1", "2", "3"]:
                    if release_time and release_time != "000000":
                        return "해제됨"
                    else:
                        return "발동중"
                elif trigger_type == "4":
                    return "해제됨"
                else:
                    return "정상"
            
            # 데이터 정리
            processed_data = {
                "symbol": symbol,
                "symbol_name": symbol_name,
                "trading_info": {
                    "total_volume": total_volume,
                    "total_amount": total_amount,
                    "execution_time": format_time(execution_time) if execution_time else None,
                },
                "vi_info": {
                    "trigger_type": vi_trigger_type,
                    "trigger_description": get_vi_trigger_description(vi_trigger_type),
                    "status": get_vi_status(vi_trigger_type, vi_release_time),
                    "trigger_price": parse_int(vi_trigger_price),
                    "release_time": format_time(vi_release_time) if vi_release_time and vi_release_time != "000000" else None,
                    "apply_type": vi_apply_type,
                    "price_change_rate": parse_float_with_sign(vi_price_change_rate),
                    "trigger_count": parse_int(vi_trigger_count),
                    "trigger_direction": trigger_direction,
                    "trigger_direction_desc": get_trigger_direction_description(trigger_direction),
                },
                "market_info": {
                    "market_type": market_type,
                    "market_description": get_market_description(market_type),
                    "pre_market_type": pre_market_type,
                    "pre_market_description": get_pre_market_description(pre_market_type),
                },
                "price_info": {
                    "static_base_price": parse_int(static_base_price),
                    "dynamic_base_price": parse_int(dynamic_base_price),
                    "static_deviation": parse_float_with_sign(static_deviation),
                    "dynamic_deviation": parse_float_with_sign(dynamic_deviation),
                },
                "extra_info": {
                    "extra_item": extra_item,
                },
                "raw_data": data.values
            }
            
            # 콜백 실행
            await self.execute_callbacks(data)
            
            # 간결한 로깅 (VI 정보)
            vi_desc = get_vi_trigger_description(vi_trigger_type)
            market_desc = get_market_description(market_type)
            direction_desc = get_trigger_direction_description(trigger_direction)
            status = get_vi_status(vi_trigger_type, vi_release_time)
            formatted_exec_time = format_time(execution_time) if execution_time else execution_time
            formatted_release_time = format_time(vi_release_time) if vi_release_time and vi_release_time != "000000" else "미해제"
            
            print(f"🚨 VI발동/해제 ({symbol}-{symbol_name}): {formatted_exec_time} "
                  f"상태={vi_desc}({status}) 가격={vi_trigger_price}원 "
                  f"방향={direction_desc} 시장={market_desc} "
                  f"해제={formatted_release_time} 적용={vi_apply_type} "
                  f"필드수={len(data.values)}")
            
            return processed_data
            
        except Exception as e:
            print(f"❌ VI발동/해제 처리 오류: {e}")
            return None




class BalanceHandler(BaseRealtimeHandler):
    """04: 잔고 핸들러"""
    
    def __init__(self):
        super().__init__("04")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """잔고 데이터 처리"""
        try:
            values = data.values
            
            # 기본 정보 추출
            account_no = values.get("9201", "")
            symbol = values.get("9001", "")
            stock_name = values.get("302", "")
            
            # 현재 시세 정보
            current_price = self._safe_int(values.get("10", "0"))
            sell_price = self._safe_int(values.get("27", "0"))
            buy_price = self._safe_int(values.get("28", "0"))
            base_price = self._safe_int(values.get("307", "0"))
            
            # 보유 정보
            holding_qty = self._safe_int(values.get("930", "0"))
            avg_price = self._safe_int(values.get("931", "0"))
            total_buy_amount = self._safe_int(values.get("932", "0"))
            tradable_qty = self._safe_int(values.get("933", "0"))
            
            # 당일 거래 정보
            today_net_qty = self._safe_int(values.get("945", "0"))
            trade_type = values.get("946", "")
            total_sell_pl = self._safe_int(values.get("950", "0"))
            
            # 손익 정보
            profit_rate = self._safe_float(values.get("8019", "0.00"))
            
            # 신용 정보  
            credit_amount = self._safe_int(values.get("957", "0"))
            credit_interest = self._safe_int(values.get("958", "0"))
            credit_type = values.get("917", "")
            loan_date = values.get("916", "")
            maturity_date = values.get("918", "")
            collateral_qty = self._safe_int(values.get("959", "0"))
            
            # 당일 실현손익
            today_realized_pl_stock = self._safe_int(values.get("990", "0"))
            today_realized_rate_stock = self._safe_float(values.get("991", "0.00"))
            today_realized_pl_credit = self._safe_int(values.get("992", "0"))
            today_realized_rate_credit = self._safe_float(values.get("993", "0.00"))
            
            # 포지션 분석
            position_analysis = self._analyze_position(
                holding_qty, current_price, avg_price, profit_rate
            )
            
            # 신용거래 분석
            credit_analysis = self._analyze_credit(
                credit_type, credit_amount, credit_interest, loan_date, maturity_date
            )
            
            # 거래 가능성 분석
            trading_analysis = self._analyze_trading_capacity(
                holding_qty, tradable_qty, today_net_qty
            )
            
            # 손익 분석
            pl_analysis = self._analyze_profit_loss(
                current_price, avg_price, holding_qty, profit_rate,
                today_realized_pl_stock, today_realized_pl_credit
            )
            
            balance_info = {
                # 기본 정보
                "account_no": account_no,
                "symbol": symbol,
                "stock_name": stock_name,
                
                # 현재 시세
                "current_price": current_price,
                "sell_price": sell_price,
                "buy_price": buy_price, 
                "base_price": base_price,
                
                # 보유 정보
                "holding_qty": holding_qty,
                "avg_price": avg_price,
                "total_buy_amount": total_buy_amount,
                "tradable_qty": tradable_qty,
                
                # 당일 거래
                "today_net_qty": today_net_qty,
                "trade_type": self._get_trade_type_desc(trade_type),
                "total_sell_pl": total_sell_pl,
                
                # 손익률
                "profit_rate": profit_rate,
                
                # 신용 정보
                "credit_type": self._get_credit_type_desc(credit_type),
                "credit_amount": credit_amount,
                "credit_interest": credit_interest,
                "loan_date": loan_date,
                "maturity_date": maturity_date,
                "collateral_qty": collateral_qty,
                
                # 당일 실현손익
                "today_realized_pl_stock": today_realized_pl_stock,
                "today_realized_rate_stock": today_realized_rate_stock,
                "today_realized_pl_credit": today_realized_pl_credit,
                "today_realized_rate_credit": today_realized_rate_credit,
                
                # 분석 결과
                "position_analysis": position_analysis,
                "credit_analysis": credit_analysis,
                "trading_analysis": trading_analysis,
                "pl_analysis": pl_analysis
            }
            
            return {
                "type": "04",
                "name": "잔고",
                "symbol": symbol,
                "data": balance_info,
                "timestamp": self._get_current_time(),
                "analysis": {
                    "position_status": position_analysis["status"],
                    "pl_status": pl_analysis["status"],
                    "trading_capacity": trading_analysis["capacity"],
                    "credit_status": credit_analysis["status"]
                }
            }
            
        except Exception as e:
            print(f"❌ 04 (잔고) 데이터 처리 실패: {e}")
            return None
    
    def _analyze_position(self, holding_qty: int, current_price: int, avg_price: int, profit_rate: float) -> Dict[str, Any]:
        """포지션 분석"""
        if holding_qty == 0:
            return {
                "status": "보유없음",
                "position_value": 0,
                "unrealized_pl": 0,
                "position_type": "현금"
            }
        
        position_value = holding_qty * current_price
        unrealized_pl = holding_qty * (current_price - avg_price)
        
        if profit_rate > 10.0:
            status = "대폭익"
        elif profit_rate > 5.0:
            status = "수익"
        elif profit_rate > 0:
            status = "소폭익"
        elif profit_rate > -5.0:
            status = "소폭손"
        elif profit_rate > -10.0:
            status = "손실"
        else:
            status = "대폭손"
        
        position_type = "매수포지션" if holding_qty > 0 else "매도포지션"
        
        return {
            "status": status,
            "position_value": position_value,
            "unrealized_pl": unrealized_pl,
            "position_type": position_type,
            "profit_rate": profit_rate
        }
    
    def _analyze_credit(self, credit_type: str, credit_amount: int, 
                       credit_interest: int, loan_date: str, maturity_date: str) -> Dict[str, Any]:
        """신용거래 분석"""
        if credit_type == "00" or credit_amount == 0:
            return {
                "status": "현금거래",
                "risk_level": "낮음",
                "interest_burden": 0
            }
        
        # 신용거래 위험도 분석
        if credit_amount > 50000000:  # 5천만원 이상
            risk_level = "높음"
        elif credit_amount > 10000000:  # 1천만원 이상
            risk_level = "보통"
        else:
            risk_level = "낮음"
        
        return {
            "status": "신용거래",
            "risk_level": risk_level,
            "interest_burden": credit_interest,
            "loan_period": f"{loan_date} ~ {maturity_date}"
        }
    
    def _analyze_trading_capacity(self, holding_qty: int, tradable_qty: int, today_net_qty: int) -> Dict[str, Any]:
        """거래 가능성 분석"""
        if tradable_qty == 0:
            capacity = "거래불가"
            reason = "매도가능수량 없음"
        elif tradable_qty == holding_qty:
            capacity = "전량매도가능"
            reason = "모든 수량 매도 가능"
        else:
            capacity = "일부매도가능"
            reason = f"{tradable_qty}주 매도 가능"
        
        # 당일 순매수량 기준 활동성 분석
        if abs(today_net_qty) > holding_qty * 0.1:  # 10% 이상
            activity = "활발"
        elif abs(today_net_qty) > 0:
            activity = "보통"
        else:
            activity = "없음"
        
        return {
            "capacity": capacity,
            "reason": reason,
            "tradable_qty": tradable_qty,
            "today_activity": activity,
            "net_trading": today_net_qty
        }
    
    def _analyze_profit_loss(self, current_price: int, avg_price: int, holding_qty: int,
                           profit_rate: float, realized_pl_stock: int, realized_pl_credit: int) -> Dict[str, Any]:
        """손익 분석"""
        unrealized_pl = holding_qty * (current_price - avg_price) if holding_qty > 0 else 0
        total_realized_pl = realized_pl_stock + realized_pl_credit
        
        # 손익 상태 분석
        if unrealized_pl > 0 and total_realized_pl > 0:
            status = "수익확대"
        elif unrealized_pl > 0:
            status = "미실현수익"
        elif total_realized_pl > 0:
            status = "실현수익"
        elif unrealized_pl < 0 and total_realized_pl < 0:
            status = "손실확대"
        elif unrealized_pl < 0:
            status = "미실현손실"
        else:
            status = "손익균형"
        
        return {
            "status": status,
            "unrealized_pl": unrealized_pl,
            "realized_pl_total": total_realized_pl,
            "realized_pl_stock": realized_pl_stock,
            "realized_pl_credit": realized_pl_credit,
            "profit_rate": profit_rate
        }
    
    def _get_trade_type_desc(self, trade_type: str) -> str:
        """매매구분 설명"""
        trade_types = {
            "1": "매수",
            "2": "매도", 
            "": "거래없음"
        }
        return trade_types.get(trade_type, f"알수없음({trade_type})")
    
    def _get_credit_type_desc(self, credit_type: str) -> str:
        """신용구분 설명"""
        credit_types = {
            "00": "현금",
            "03": "유통융자",
            "05": "자기융자",
            "06": "유통대주", 
            "07": "자기대주",
            "": "현금"
        }
        return credit_types.get(credit_type, f"알수없음({credit_type})")

