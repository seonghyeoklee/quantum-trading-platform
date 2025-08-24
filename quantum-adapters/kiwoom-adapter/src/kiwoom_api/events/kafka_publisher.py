"""
Kafka 이벤트 발행자

키움 API 데이터를 Kafka로 비동기 발행하는 Publisher
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Union, List
from contextlib import asynccontextmanager

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError

from .event_schemas import BaseEvent, EventType


logger = logging.getLogger(__name__)


class KafkaEventPublisher:
    """비동기 Kafka 이벤트 발행자"""
    
    def __init__(
        self, 
        bootstrap_servers: str = "quantum-kafka:9092",
        enable_kafka: bool = True,
        batch_size: int = 100,
        max_batch_size: int = 16384
    ):
        self.bootstrap_servers = bootstrap_servers
        self.enable_kafka = enable_kafka
        self.batch_size = batch_size
        self.max_batch_size = max_batch_size
        
        self.producer: Optional[AIOKafkaProducer] = None
        self.is_connected = False
        self._batch_buffer: List[tuple] = []
        self._last_flush = datetime.now()
        
        # 토픽 설정 (기존 등록된 토픽에 맞춤)
        self.topics = {
            EventType.STOCK_TRADE: "kiwoom.realtime.quote",      # 실시간 시세/체결 → quote
            EventType.STOCK_PRICE: "kiwoom.realtime.quote",      # 실시간 현재가 → quote
            EventType.ORDER_BOOK: "kiwoom.realtime.quote",       # 실시간 호가 → quote
            EventType.ORDER_EXECUTED: "kiwoom.realtime.order",   # 거래 주문 → order
            EventType.ORDER_FAILED: "kiwoom.realtime.order",     # 주문 실패 → order
            EventType.MARKET_DATA: "kiwoom.realtime.general",    # 시장 데이터 → general
            EventType.SCREENING_SIGNAL: "kiwoom.realtime.screener", # 조건검색 → screener
            EventType.API_RESPONSE: "kiwoom.realtime.general",   # 일반 API → general
            EventType.API_ERROR: "kiwoom.realtime.general"       # 에러 이벤트 → general
        }
        
        logger.info(f"KafkaEventPublisher 초기화 - 활성화: {enable_kafka}")
        
    async def start(self):
        """Kafka Producer 시작"""
        if not self.enable_kafka:
            logger.info("Kafka 비활성화 상태 - 이벤트는 로그로만 출력됩니다")
            return
            
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=self._serialize_event,
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # 모든 레플리카에서 확인
                compression_type='gzip',
                request_timeout_ms=30000,
                enable_idempotence=True  # 중복 방지
            )
            
            await self.producer.start()
            self.is_connected = True
            logger.info(f"✅ Kafka Producer 연결 성공: {self.bootstrap_servers}")
            
            # 배치 플러시 태스크 시작
            asyncio.create_task(self._batch_flush_worker())
            
        except Exception as e:
            logger.error(f"❌ Kafka Producer 연결 실패: {e}")
            self.is_connected = False
            
    async def stop(self):
        """Kafka Producer 종료"""
        if self.producer and self.is_connected:
            try:
                # 남은 배치 플러시
                await self._flush_batch()
                await self.producer.stop()
                self.is_connected = False
                logger.info("Kafka Producer 연결 종료")
            except Exception as e:
                logger.error(f"Kafka Producer 종료 중 오류: {e}")
                
    def _serialize_event(self, event_data: Union[Dict, BaseEvent]) -> bytes:
        """이벤트 직렬화"""
        if isinstance(event_data, BaseEvent):
            data = event_data.model_dump(mode='json')
        else:
            data = event_data
            
        return json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
        
    def _get_topic_name(self, event_type: Union[EventType, str]) -> str:
        """이벤트 타입에 따른 토픽명 결정"""
        if isinstance(event_type, str):
            try:
                event_type = EventType(event_type)
            except ValueError:
                return "kiwoom.misc.events"  # 기본 토픽
                
        return self.topics.get(event_type, "kiwoom.misc.events")
        
    async def publish_event(
        self, 
        event: Union[BaseEvent, Dict[str, Any]],
        topic: Optional[str] = None,
        key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """단일 이벤트 발행"""
        try:
            # 이벤트 데이터 준비
            if isinstance(event, BaseEvent):
                event_type = event.event_type
                event_data = event
                if not key:
                    key = getattr(event, 'symbol', None) or event.event_id
            else:
                event_type = event.get('event_type', EventType.API_RESPONSE)
                event_data = event
                if not key:
                    key = event.get('symbol') or str(uuid.uuid4())
            
            # 토픽 결정
            if not topic:
                topic = self._get_topic_name(event_type)
                
            # Kafka 비활성화 시 로그만 출력
            if not self.enable_kafka:
                logger.info(f"📤 [MOCK] Event발행: {topic} - {event_type}")
                return True
                
            if not self.is_connected:
                logger.warning("Kafka 연결 끊김 - 이벤트 발행 실패")
                return False
                
            # Kafka로 전송
            await self.producer.send_and_wait(
                topic=topic,
                value=event_data,
                key=key,
                headers=self._prepare_headers(headers)
            )
            
            logger.debug(f"📤 이벤트 발행 성공: {topic} - {event_type}")
            return True
            
        except KafkaError as e:
            logger.error(f"❌ Kafka 이벤트 발행 실패: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 이벤트 발행 중 예외: {e}")
            return False
            
    async def publish_batch(
        self, 
        events: List[Union[BaseEvent, Dict[str, Any]]],
        topic: Optional[str] = None
    ) -> int:
        """배치 이벤트 발행"""
        if not events:
            return 0
            
        success_count = 0
        
        if not self.enable_kafka:
            logger.info(f"📤 [MOCK] 배치 Event발행: {len(events)}개 이벤트")
            return len(events)
            
        if not self.is_connected:
            logger.warning("Kafka 연결 끊김 - 배치 이벤트 발행 실패")
            return 0
            
        try:
            # 배치로 전송
            for event in events:
                if isinstance(event, BaseEvent):
                    event_topic = topic or self._get_topic_name(event.event_type)
                    key = getattr(event, 'symbol', None) or event.event_id
                else:
                    event_topic = topic or self._get_topic_name(event.get('event_type'))
                    key = event.get('symbol') or str(uuid.uuid4())
                    
                await self.producer.send(
                    topic=event_topic,
                    value=event,
                    key=key
                )
                success_count += 1
                
            # 배치 전송
            await self.producer.flush()
            logger.info(f"📤 배치 이벤트 발행 성공: {success_count}개")
            
        except Exception as e:
            logger.error(f"❌ 배치 이벤트 발행 실패: {e}")
            
        return success_count
        
    def _prepare_headers(self, headers: Optional[Dict[str, str]]) -> Optional[List[tuple]]:
        """헤더 준비"""
        if not headers:
            headers = {}
            
        headers.update({
            'source': 'kiwoom_adapter',
            'timestamp': datetime.now().isoformat(),
            'content-type': 'application/json'
        })
        
        return [(k, v.encode('utf-8')) for k, v in headers.items()]
        
    async def _batch_flush_worker(self):
        """배치 플러시 워커 (백그라운드 태스크)"""
        while self.is_connected:
            try:
                await asyncio.sleep(1.0)  # 1초마다 체크
                
                if (datetime.now() - self._last_flush).seconds >= 5:  # 5초마다 플러시
                    await self._flush_batch()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"배치 플러시 워커 오류: {e}")
                
    async def _flush_batch(self):
        """배치 버퍼 플러시"""
        if not self._batch_buffer or not self.is_connected:
            return
            
        try:
            # 버퍼에 있는 이벤트들 전송
            for topic, key, value in self._batch_buffer:
                await self.producer.send(topic=topic, key=key, value=value)
                
            await self.producer.flush()
            batch_size = len(self._batch_buffer)
            self._batch_buffer.clear()
            self._last_flush = datetime.now()
            
            logger.debug(f"배치 플러시 완료: {batch_size}개 이벤트")
            
        except Exception as e:
            logger.error(f"배치 플러시 실패: {e}")
            
    async def get_connection_info(self) -> Dict[str, Any]:
        """연결 정보 반환"""
        return {
            'bootstrap_servers': self.bootstrap_servers,
            'is_connected': self.is_connected,
            'enable_kafka': self.enable_kafka,
            'topics': self.topics,
            'batch_buffer_size': len(self._batch_buffer)
        }


# 전역 Publisher 인스턴스 (싱글톤 패턴)
_global_publisher: Optional[KafkaEventPublisher] = None


async def get_kafka_publisher() -> KafkaEventPublisher:
    """전역 Kafka Publisher 인스턴스 반환"""
    global _global_publisher
    
    if _global_publisher is None:
        # 환경 변수에서 설정 읽기
        import os
        
        enable_kafka = os.getenv('ENABLE_KAFKA', 'true').lower() == 'true'
        bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'quantum-kafka:9092')
        
        _global_publisher = KafkaEventPublisher(
            bootstrap_servers=bootstrap_servers,
            enable_kafka=enable_kafka
        )
        
        if enable_kafka:
            await _global_publisher.start()
            
    return _global_publisher


@asynccontextmanager
async def kafka_publisher_context():
    """Kafka Publisher 컨텍스트 매니저"""
    publisher = await get_kafka_publisher()
    try:
        yield publisher
    finally:
        if publisher and publisher.enable_kafka:
            await publisher.stop()