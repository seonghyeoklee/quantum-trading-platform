"""
FastAPI 미들웨어를 통한 API 응답 이벤트 발행

모든 REST API 응답을 Kafka 이벤트로 자동 발행
"""

import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .kafka_publisher import get_kafka_publisher
from .event_schemas import APIResponseEvent, MarketDataEvent, OrderExecutedEvent, APIErrorEvent
from .error_codes import KiwoomErrorCodes, should_alert


class KafkaEventMiddleware(BaseHTTPMiddleware):
    """API 응답을 자동으로 Kafka 이벤트로 발행하는 미들웨어"""
    
    def __init__(self, app, enable_kafka: bool = True):
        super().__init__(app)
        self.enable_kafka = enable_kafka
        self.kafka_publisher = None
        
        # 이벤트 발행 대상 API 패턴
        self.api_patterns = {
            '/api/fn_ka': 'market_data',      # 시장 데이터 조회 API
            '/api/fn_kt': 'trading_order',    # 거래 주문 API
            '/api/fn_au': 'auth',             # 인증 API
        }
        
        # 차트 API는 발행 제외 (대용량 데이터)
        self.chart_api_exclusions = {
            '/api/fn_ka10080',  # 주식분봉차트조회
            '/api/fn_ka10081',  # 주식일봉차트조회
            '/api/fn_ka10082',  # 주식주봉차트조회
            '/api/fn_ka10083',  # 주식월봉차트조회
            '/api/fn_ka10094',  # 주식년봉차트조회
            '/api/fn_ka10079',  # 주식틱차트조회
            '/api/fn_ka20004',  # 업종틱차트조회
            '/api/fn_ka20005',  # 업종분봉조회
            '/api/fn_ka20006',  # 업종일봉조회
            '/api/fn_ka20007',  # 업종주봉조회
            '/api/fn_ka20008',  # 업종월봉조회
            '/api/fn_ka20019',  # 업종년봉조회
            '/api/fn_ka10060',  # 종목별투자자기관별차트조회
            '/api/fn_ka10064',  # 장중투자자별매매차트조회
        }
        
    async def dispatch(self, request: Request, call_next):
        """HTTP 요청/응답 처리 및 이벤트 발행"""
        
        # Kafka Publisher 초기화 (lazy loading)
        if self.enable_kafka and not self.kafka_publisher:
            try:
                self.kafka_publisher = await get_kafka_publisher()
            except Exception as e:
                # Kafka 초기화 실패 시 로깅만 하고 계속 진행
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Kafka Publisher 초기화 실패: {e}")
                self.enable_kafka = False
        
        # 요청 시작 시간
        start_time = time.time()
        
        # 요청 데이터 수집 
        request_data = await self._extract_request_data(request)
        
        # 다음 미들웨어/엔드포인트 호출
        response = await call_next(request)
        
        # 응답 시간 계산
        response_time_ms = (time.time() - start_time) * 1000
        
        # 응답 데이터 수집 및 이벤트 발행
        if self._should_publish_event(request):
            await self._publish_api_event(
                request, 
                response, 
                request_data,
                response_time_ms
            )
            
        # 에러 감지 및 에러 이벤트 발행
        if self.enable_kafka and response.status_code >= 400:
            await self._check_and_publish_error_event(
                request,
                response,
                request_data,
                response_time_ms
            )
        
        return response
        
    async def _extract_request_data(self, request: Request) -> Optional[Dict[str, Any]]:
        """요청 데이터 추출"""
        request_data = None
        
        try:
            # POST/PUT 요청의 경우 바디 데이터 추출
            if request.method in ['POST', 'PUT', 'PATCH']:
                # Content-Type 확인
                content_type = request.headers.get('content-type', '')
                
                if 'application/json' in content_type:
                    # 바디를 한 번만 읽기 위해 복사
                    body = await request.body()
                    if body:
                        request_data = json.loads(body.decode('utf-8'))
                        
            # GET 요청의 경우 쿼리 파라미터 추출
            elif request.method == 'GET':
                request_data = dict(request.query_params)
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"요청 데이터 추출 실패: {e}")
            
        return request_data
        
    def _should_publish_event(self, request: Request) -> bool:
        """이벤트 발행 대상인지 확인"""
        if not self.enable_kafka:
            return False
            
        path = request.url.path
        
        # 차트 API는 발행 제외 (대용량 데이터)
        if path in self.chart_api_exclusions:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"📊 차트 API 이벤트 발행 제외: {path}")
            return False
            
        # 키움 API 경로만 대상
        for pattern in self.api_patterns.keys():
            if path.startswith(pattern):
                return True
                
        return False
        
    async def _publish_api_event(
        self,
        request: Request,
        response: Response, 
        request_data: Optional[Dict[str, Any]],
        response_time_ms: float
    ):
        """API 이벤트 발행"""
        try:
            if not self.kafka_publisher:
                return
                
            # 응답 데이터 추출
            response_data = await self._extract_response_data(response)
            
            # API 타입에 따른 이벤트 생성
            api_type = self._get_api_type(request.url.path)
            
            if api_type == 'market_data':
                event = await self._create_market_data_event(
                    request, response, request_data, response_data, response_time_ms
                )
            elif api_type == 'trading_order':
                event = await self._create_trading_event(
                    request, response, request_data, response_data, response_time_ms
                )
            else:
                event = await self._create_general_api_event(
                    request, response, request_data, response_data, response_time_ms
                )
                
            if event:
                # Kafka로 이벤트 발행
                success = await self.kafka_publisher.publish_event(event)
                if success:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"📤 API 이벤트 발행: {request.url.path}")
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"API 이벤트 발행 실패: {e}")
            
    async def _extract_response_data(self, response: Response) -> Dict[str, Any]:
        """응답 데이터 추출"""
        try:
            # 응답 바디가 있는 경우만 처리
            if hasattr(response, 'body'):
                body = response.body
                if body:
                    return json.loads(body.decode('utf-8'))
        except Exception:
            pass
            
        return {}
        
    def _get_api_type(self, path: str) -> str:
        """API 경로에서 타입 추출"""
        for pattern, api_type in self.api_patterns.items():
            if path.startswith(pattern):
                return api_type
        return 'general'
        
    async def _create_market_data_event(
        self,
        request: Request,
        response: Response,
        request_data: Optional[Dict[str, Any]],
        response_data: Dict[str, Any],
        response_time_ms: float
    ) -> Optional[MarketDataEvent]:
        """시장 데이터 이벤트 생성"""
        try:
            # API ID 추출 (fn_ka10001 등)
            path_parts = request.url.path.split('/')
            api_id = path_parts[-1] if path_parts else 'unknown'
            
            # 연속조회 정보
            cont_yn = request.query_params.get('cont_yn', 'N')
            next_key = request.query_params.get('next_key', '')
            
            return MarketDataEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                api_id=api_id,
                request_data=request_data or {},
                response_data=response_data,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                cont_yn=cont_yn,
                next_key=next_key if next_key else None
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"시장 데이터 이벤트 생성 실패: {e}")
            return None
            
    async def _create_trading_event(
        self,
        request: Request,
        response: Response,
        request_data: Optional[Dict[str, Any]],
        response_data: Dict[str, Any],
        response_time_ms: float
    ) -> Optional[OrderExecutedEvent]:
        """거래 이벤트 생성"""
        try:
            if response.status_code != 200 or not response_data.get('Body'):
                return None
                
            body = response_data.get('Body', {})
            
            # 주문번호가 있는 경우만 이벤트 생성 (체결 성공)
            order_id = body.get('ord_no')
            if not order_id:
                return None
                
            # API 타입에 따른 매매구분 결정
            api_path = request.url.path
            if 'fn_kt10000' in api_path:
                side = 'buy'
                order_type = '매수주문'
            elif 'fn_kt10001' in api_path:
                side = 'sell'  
                order_type = '매도주문'
            elif 'fn_kt10002' in api_path:
                side = 'modify'
                order_type = '정정주문'
            elif 'fn_kt10003' in api_path:
                side = 'cancel'
                order_type = '취소주문'
            else:
                side = 'unknown'
                order_type = '알수없음'
                
            return OrderExecutedEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                order_id=order_id,
                symbol=request_data.get('stk_cd', '') if request_data else '',
                side=side,
                order_type=order_type,
                quantity=int(request_data.get('ord_qty', 0)) if request_data else 0,
                price=int(request_data.get('ord_uv', 0)) if request_data else 0,
                executed_quantity=0,  # API 응답에서 추출 필요
                executed_price=0,     # API 응답에서 추출 필요
                remaining_quantity=0, # API 응답에서 추출 필요
                exchange=body.get('dmst_stex_tp', ''),
                order_status='submitted'
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"거래 이벤트 생성 실패: {e}")
            return None
            
    async def _create_general_api_event(
        self,
        request: Request,
        response: Response,
        request_data: Optional[Dict[str, Any]],
        response_data: Dict[str, Any],
        response_time_ms: float
    ) -> Optional[APIResponseEvent]:
        """일반 API 이벤트 생성"""
        try:
            return APIResponseEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                api_endpoint=request.url.path,
                http_method=request.method,
                request_id=request.headers.get('x-request-id'),
                request_data=request_data,
                response_data=response_data,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                error_message=response_data.get('error') if response.status_code >= 400 else None
            )
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"일반 API 이벤트 생성 실패: {e}")
            return None
            
    async def _check_and_publish_error_event(
        self,
        request: Request,
        response: Response,
        request_data: Optional[Dict[str, Any]],
        response_time_ms: float
    ):
        """키움 API 에러 감지 및 에러 이벤트 발행"""
        try:
            if not self.kafka_publisher:
                return
                
            # 응답 데이터 추출
            response_data = await self._extract_response_data(response)
            
            # 키움 에러 코드 감지
            error_code = self._extract_kiwoom_error_code(response_data)
            if not error_code:
                # 키움 에러 코드가 없으면 HTTP 에러로만 처리
                return
                
            # 키움 에러 정보 조회
            error_info = KiwoomErrorCodes.get_error(error_code)
            if not error_info:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"알 수 없는 키움 에러 코드: {error_code}")
                return
                
            # 에러 이벤트 생성
            error_event = APIErrorEvent(
                event_id=str(uuid.uuid4()),
                timestamp=datetime.now(),
                error_code=error_code,
                error_message=error_info.message,
                severity=error_info.severity.value,
                category=error_info.category.value,
                api_endpoint=request.url.path,
                http_method=request.method,
                request_data=request_data or {},
                response_data=response_data,
                auto_retry=error_info.auto_retry,
                recovery_action=error_info.recovery_action,
                response_time_ms=response_time_ms,
                http_status_code=response.status_code
            )
            
            # Kafka로 에러 이벤트 발행
            success = await self.kafka_publisher.publish_event(error_event)
            if success:
                import logging
                logger = logging.getLogger(__name__)
                
                # 심각한 에러는 경고 로그
                if should_alert(error_code):
                    logger.error(f"🚨 키움 에러 발생 [{error_code}]: {error_info.message} - API: {request.url.path}")
                else:
                    logger.warning(f"⚠️ 키움 에러 [{error_code}]: {error_info.message} - API: {request.url.path}")
                    
                # 자동 복구 가능한 에러인 경우 추가 로깅
                if error_info.auto_retry:
                    logger.info(f"🔄 자동 복구 가능: {error_info.recovery_action}")
                    
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"에러 이벤트 발행 실패: {e}")
            
    def _extract_kiwoom_error_code(self, response_data: Dict[str, Any]) -> Optional[str]:
        """키움 응답에서 에러 코드 추출"""
        try:
            # 키움 API 표준 응답 구조에서 에러 코드 추출
            if "Body" in response_data:
                body = response_data["Body"]
                # return_code가 0이 아니면 에러
                return_code = body.get("return_code")
                if return_code and str(return_code) != "0":
                    return str(return_code)
                    
            # Header에서 에러 정보 확인
            if "Header" in response_data:
                header = response_data["Header"]
                error_code = header.get("error_code")
                if error_code:
                    return str(error_code)
                    
            # 직접적인 error 필드 확인
            if "error" in response_data:
                error_info = response_data["error"]
                if isinstance(error_info, dict):
                    error_code = error_info.get("code")
                    if error_code:
                        return str(error_code)
                        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"에러 코드 추출 실패: {e}")
            
        return None