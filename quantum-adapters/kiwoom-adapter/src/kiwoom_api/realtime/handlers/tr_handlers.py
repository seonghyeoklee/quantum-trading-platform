"""
키움증권 조건검색 TR 핸들러 모듈

TR 명령어별 전용 핸들러로 조건검색 기능 제공:
- CNSRLST: 조건검색 목록조회
- CNSRREQ: 조건검색 실행 (일반/실시간)  
- CNSRCLR: 조건검색 실시간 해제
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

# Handle both relative and absolute imports
try:
    from ..models.realtime_data import RealtimeData
    from .base_handler import BaseRealtimeHandler
except ImportError:
    from kiwoom_api.realtime.models.realtime_data import RealtimeData
    from kiwoom_api.realtime.handlers.base_handler import BaseRealtimeHandler

logger = logging.getLogger(__name__)


class BaseTRHandler(ABC):
    """조건검색 TR 핸들러 베이스 클래스"""
    
    def __init__(self, tr_name: str):
        self.tr_name = tr_name
        
    @abstractmethod
    async def handle(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """TR 응답 처리"""
        pass
        
    def _safe_int(self, value: str) -> int:
        """안전한 정수 변환"""
        try:
            return int(value) if value else 0
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value: str) -> float:
        """안전한 실수 변환"""
        try:
            return float(value) if value else 0.0
        except (ValueError, TypeError):
            return 0.0
            
    def _get_current_time(self) -> str:
        """현재 시간 반환"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")


class ScreenerListHandler(BaseTRHandler):
    """CNSRLST: 조건검색 목록조회 핸들러"""
    
    def __init__(self):
        super().__init__("CNSRLST")
        
    async def handle(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """조건검색 목록 응답 처리
        
        응답 형태:
        {
            'trnm': 'CNSRLST',
            'return_code': 0,
            'data': [['0','조건1'], ['1','조건2'], ...]
        }
        """
        try:
            return_code = response_data.get('return_code', -1)
            return_msg = response_data.get('return_msg', '')
            
            if return_code != 0:
                logger.error(f"조건검색 목록조회 실패: {return_msg}")
                return {
                    "tr_name": "CNSRLST",
                    "success": False,
                    "error_message": return_msg,
                    "conditions": []
                }
            
            # 조건검색식 목록 파싱
            raw_conditions = response_data.get('data', [])
            conditions = []
            
            for condition_data in raw_conditions:
                if len(condition_data) >= 2:
                    conditions.append({
                        "seq": condition_data[0],
                        "name": condition_data[1],
                        "description": f"조건식 {condition_data[0]}: {condition_data[1]}"
                    })
            
            logger.info(f"조건검색 목록 조회 성공: {len(conditions)}개 조건식")
            
            return {
                "tr_name": "CNSRLST",
                "success": True,
                "total_count": len(conditions),
                "conditions": conditions,
                "timestamp": self._get_current_time(),
                "analysis": {
                    "available_conditions": len(conditions),
                    "condition_types": "사용자 정의 조건식",
                    "status": "조회완료"
                }
            }
            
        except Exception as e:
            logger.error(f"조건검색 목록조회 처리 실패: {e}")
            return {
                "tr_name": "CNSRLST",
                "success": False,
                "error_message": str(e),
                "conditions": []
            }


class ScreenerSearchHandler(BaseTRHandler):
    """CNSRREQ: 조건검색 실행 핸들러"""
    
    def __init__(self):
        super().__init__("CNSRREQ")
        
    async def handle(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """조건검색 실행 응답 처리
        
        요청 형태:
        {
            'trnm': 'CNSRREQ',
            'seq': '1',
            'search_type': '0' or '1',  # 0:일반, 1:실시간포함
            'stex_tp': 'K'
        }
        
        응답 형태 (일반 검색):
        {
            'trnm': 'CNSRREQ',
            'return_code': 0,
            'seq': '1',
            'data': [{'jmcode': '005930'}, ...]
        }
        
        응답 형태 (실시간 검색):
        {
            'trnm': 'CNSRREQ', 
            'return_code': 0,
            'seq': '1',
            'data': [{'jmcode': '005930'}]
        } + 이후 REAL 메시지로 실시간 수신
        """
        try:
            return_code = response_data.get('return_code', -1)
            return_msg = response_data.get('return_msg', '')
            seq = response_data.get('seq', request_data.get('seq', ''))
            
            if return_code != 0:
                logger.error(f"조건검색 실행 실패 (seq={seq}): {return_msg}")
                return {
                    "tr_name": "CNSRREQ",
                    "seq": seq,
                    "success": False,
                    "error_message": return_msg,
                    "search_results": []
                }
            
            # 검색 결과 파싱
            raw_results = response_data.get('data', [])
            search_results = []
            
            for result_data in raw_results:
                if isinstance(result_data, dict) and 'jmcode' in result_data:
                    search_results.append({
                        "stock_code": result_data['jmcode'],
                        "detected_time": self._get_current_time()
                    })
            
            # 검색 타입 분석
            search_type = request_data.get('search_type', '0')
            is_realtime = search_type == '1'
            
            logger.info(f"조건검색 실행 성공 (seq={seq}): {len(search_results)}개 종목, 실시간={'ON' if is_realtime else 'OFF'}")
            
            return {
                "tr_name": "CNSRREQ",
                "seq": seq,
                "success": True,
                "search_type": search_type,
                "realtime_enabled": is_realtime,
                "total_results": len(search_results),
                "search_results": search_results,
                "timestamp": self._get_current_time(),
                "analysis": {
                    "result_count": len(search_results),
                    "search_mode": "실시간 검색" if is_realtime else "일반 검색",
                    "status": "실시간 감시 시작됨" if is_realtime else "검색 완료",
                    "next_action": "실시간 알림 대기" if is_realtime else "추가 검색 가능"
                }
            }
            
        except Exception as e:
            logger.error(f"조건검색 실행 처리 실패: {e}")
            return {
                "tr_name": "CNSRREQ",
                "seq": request_data.get('seq', ''),
                "success": False,
                "error_message": str(e),
                "search_results": []
            }


class ScreenerClearHandler(BaseTRHandler):
    """CNSRCLR: 조건검색 실시간 해제 핸들러"""
    
    def __init__(self):
        super().__init__("CNSRCLR")
        
    async def handle(self, request_data: Dict[str, Any], response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """조건검색 실시간 해제 응답 처리
        
        요청 형태:
        {
            'trnm': 'CNSRCLR',
            'seq': '1'
        }
        
        응답 형태:
        {
            'trnm': 'CNSRCLR',
            'return_code': 0,
            'seq': '1'
        }
        """
        try:
            return_code = response_data.get('return_code', -1)
            return_msg = response_data.get('return_msg', '')
            seq = response_data.get('seq', request_data.get('seq', ''))
            
            if return_code != 0:
                logger.error(f"조건검색 실시간 해제 실패 (seq={seq}): {return_msg}")
                return {
                    "tr_name": "CNSRCLR",
                    "seq": seq,
                    "success": False,
                    "error_message": return_msg
                }
            
            logger.info(f"조건검색 실시간 해제 성공 (seq={seq})")
            
            return {
                "tr_name": "CNSRCLR",
                "seq": seq,
                "success": True,
                "timestamp": self._get_current_time(),
                "analysis": {
                    "status": "실시간 감시 중단됨",
                    "condition_seq": seq,
                    "next_action": "새로운 조건검색 실행 가능"
                }
            }
            
        except Exception as e:
            logger.error(f"조건검색 실시간 해제 처리 실패: {e}")
            return {
                "tr_name": "CNSRCLR",
                "seq": request_data.get('seq', ''),
                "success": False,
                "error_message": str(e)
            }


class ScreenerRealtimeHandler(BaseRealtimeHandler):
    """조건검색 실시간 알림 핸들러
    
    조건검색에서 발생하는 실시간 알림 처리
    기존 REAL 메시지 중 조건검색 관련 데이터 식별 및 처리
    """
    
    def __init__(self):
        super().__init__("screener_realtime")
        
    async def handle(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """조건검색 실시간 알림 처리
        
        실시간 데이터 형태:
        {
            'trnm': 'REAL',
            'data': [{
                'values': {
                    '841': '조건식번호',
                    '9001': '종목코드',
                    '843': 'I',  # I:삽입(조건만족), D:삭제(조건이탈)
                    '20': '체결시간',
                    '907': '매도/수구분'
                }
            }]
        }
        """
        try:
            values = data.values
            
            # 조건검색 실시간 데이터 식별
            condition_seq = values.get("841")  # 조건식 일련번호
            stock_code = values.get("9001")   # 종목코드
            action = values.get("843")        # I:삽입, D:삭제
            trade_time = values.get("20")     # 체결시간
            trade_side = values.get("907")    # 매도/수 구분
            
            if not condition_seq or not stock_code or not action:
                return None  # 조건검색 실시간 데이터가 아님
            
            # 액션 분석
            if action == 'I':
                action_desc = "조건만족"
                status = "종목추가"
            elif action == 'D':
                action_desc = "조건이탈"
                status = "종목제거"
            else:
                action_desc = f"알수없음({action})"
                status = "불명"
            
            # 매매 방향 분석
            trade_direction = self._get_trade_direction(trade_side)
            
            logger.info(f"조건검색 실시간 알림 - 조건:{condition_seq}, 종목:{stock_code}, 액션:{action_desc}")
            
            return {
                "type": "screener_realtime",
                "name": "조건검색실시간알림",
                "condition_seq": condition_seq,
                "stock_code": stock_code,
                "action": action,
                "action_description": action_desc,
                "status": status,
                "trade_time": trade_time,
                "trade_direction": trade_direction,
                "timestamp": self._get_current_time(),
                "analysis": {
                    "alert_type": action_desc,
                    "condition_status": status,
                    "market_signal": f"{action_desc} 신호",
                    "trade_info": f"{trade_direction} at {trade_time}" if trade_time else "시간정보없음"
                }
            }
            
        except Exception as e:
            logger.error(f"조건검색 실시간 알림 처리 실패: {e}")
            return None
    
    def _get_trade_direction(self, trade_side: str) -> str:
        """매매 방향 해석"""
        trade_directions = {
            "1": "매수",
            "2": "매도", 
            "": "정보없음"
        }
        return trade_directions.get(trade_side, f"알수없음({trade_side})")


class TRHandlerRegistry:
    """TR 핸들러 등록 및 관리"""
    
    def __init__(self):
        self.tr_handlers: Dict[str, BaseTRHandler] = {}
        self.realtime_handlers: Dict[str, BaseRealtimeHandler] = {}
        self._initialize_handlers()
        
    def _initialize_handlers(self):
        """기본 TR 핸들러들 초기화"""
        # 조건검색 TR 핸들러 등록
        self.register_tr_handler("CNSRLST", ScreenerListHandler())
        self.register_tr_handler("CNSRREQ", ScreenerSearchHandler())
        self.register_tr_handler("CNSRCLR", ScreenerClearHandler())
        
        # 조건검색 실시간 핸들러 등록
        self.register_realtime_handler("screener_realtime", ScreenerRealtimeHandler())
        
        logger.info(f"TR 핸들러 등록 완료: {list(self.tr_handlers.keys())}")
        logger.info(f"조건검색 실시간 핸들러 등록 완료")
        
    def register_tr_handler(self, tr_name: str, handler: BaseTRHandler):
        """TR 핸들러 등록"""
        self.tr_handlers[tr_name] = handler
        logger.debug(f"TR 핸들러 등록: {tr_name} -> {handler.__class__.__name__}")
        
    def register_realtime_handler(self, name: str, handler: BaseRealtimeHandler):
        """실시간 핸들러 등록"""
        self.realtime_handlers[name] = handler
        logger.debug(f"실시간 핸들러 등록: {name} -> {handler.__class__.__name__}")
        
    def has_tr_handler(self, tr_name: str) -> bool:
        """TR 핸들러 존재 여부 확인"""
        return tr_name in self.tr_handlers
        
    def get_tr_handler(self, tr_name: str) -> Optional[BaseTRHandler]:
        """TR 핸들러 반환"""
        return self.tr_handlers.get(tr_name)
        
    def get_supported_trs(self) -> List[str]:
        """지원하는 TR 목록 반환"""
        return list(self.tr_handlers.keys())
        
    async def handle_tr_response(self, tr_name: str, request_data: Dict[str, Any], 
                                response_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """TR 응답 처리"""
        handler = self.get_tr_handler(tr_name)
        if handler:
            return await handler.handle(request_data, response_data)
        else:
            logger.warning(f"지원하지 않는 TR: {tr_name}")
            return None
            
    async def handle_screener_realtime(self, data: RealtimeData) -> Optional[Dict[str, Any]]:
        """조건검색 실시간 데이터 처리"""
        handler = self.realtime_handlers.get("screener_realtime")
        if handler:
            return await handler.handle(data)
        return None