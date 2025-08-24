#!/usr/bin/env python3
"""
Kafka Consumer 테스트 스크립트

Kiwoom Adapter에서 발행된 이벤트를 수신하여 검증하는 테스트 도구
"""
import asyncio
import json
import logging
from aiokafka import AIOKafkaConsumer
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Kafka 토픽 설정 (kiwoom adapter와 동일)
TOPICS = [
    'kiwoom.realtime.trades',      # 실시간 체결 데이터
    'kiwoom.realtime.prices',      # 실시간 현재가 데이터
    'kiwoom.realtime.orderbooks',  # 실시간 호가 데이터
    'kiwoom.trading.orders',       # 거래 주문 데이터
    'kiwoom.api.market_data',      # API 마켓 데이터 
    'kiwoom.api.responses',        # API 응답 데이터
    'kiwoom.signals.screening'     # 조건검색 신호
]

async def kafka_consumer_test():
    """Kafka 컨슈머 테스트 실행"""
    
    consumer = AIOKafkaConsumer(
        *TOPICS,  # 모든 토픽 구독
        bootstrap_servers='quantum-kafka:9092',
        group_id='kiwoom_test_consumer',
        value_deserializer=lambda x: json.loads(x.decode('utf-8')) if x else None,
        auto_offset_reset='latest'  # 최신 메시지부터
    )
    
    try:
        await consumer.start()
        logger.info(f"🔄 Kafka Consumer 시작 - 토픽: {', '.join(TOPICS)}")
        
        async for msg in consumer:
            try:
                topic = msg.topic
                key = msg.key.decode('utf-8') if msg.key else None
                value = msg.value
                timestamp = datetime.fromtimestamp(msg.timestamp / 1000)
                
                logger.info(f"📥 수신: {topic}")
                logger.info(f"   - Key: {key}")
                logger.info(f"   - Timestamp: {timestamp}")
                logger.info(f"   - Event Type: {value.get('event_type', 'unknown')}")
                
                # 이벤트 타입별 상세 로깅
                if topic == 'kiwoom.realtime.trades':
                    logger.info(f"   - 종목: {value.get('symbol')} 가격: {value.get('price')} 수량: {value.get('volume')}")
                elif topic == 'kiwoom.api.responses':
                    logger.info(f"   - API: {value.get('api_endpoint')} 상태: {value.get('status_code')}")
                elif topic == 'kiwoom.trading.orders':
                    logger.info(f"   - 주문ID: {value.get('order_id')} 종목: {value.get('symbol')}")
                
                print(f"Raw Data: {json.dumps(value, indent=2, ensure_ascii=False)}")
                print("-" * 80)
                
            except Exception as e:
                logger.error(f"메시지 처리 오류: {e}")
                
    except KeyboardInterrupt:
        logger.info("🛑 Consumer 중지 요청됨")
    except Exception as e:
        logger.error(f"❌ Consumer 오류: {e}")
    finally:
        await consumer.stop()
        logger.info("✅ Kafka Consumer 종료")

if __name__ == "__main__":
    print("🔄 Kiwoom Kafka Consumer 테스트 시작...")
    print(f"구독 토픽: {', '.join(TOPICS)}")
    print("Ctrl+C로 종료")
    print("-" * 80)
    
    try:
        asyncio.run(kafka_consumer_test())
    except KeyboardInterrupt:
        print("\n👋 테스트 종료")