package com.quantum.web.events;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantum.web.service.RealtimeDataCacheService;
import com.quantum.web.service.TimeSeriesService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.support.KafkaHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.messaging.handler.annotation.Payload;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

/**
 * 실시간 데이터 이벤트 핸들러
 * 키움증권 Python 어댑터에서 발행하는 Kafka 이벤트를 수신하고 처리
 */
@Component
public class RealtimeDataEventHandler {

    private static final Logger logger = LoggerFactory.getLogger(RealtimeDataEventHandler.class);

    private final ObjectMapper objectMapper;
    private final RealtimeDataCacheService cacheService;
    private final TimeSeriesService timeSeriesService;
    private final SimpMessagingTemplate messagingTemplate;

    public RealtimeDataEventHandler(ObjectMapper objectMapper, 
                                  RealtimeDataCacheService cacheService,
                                  TimeSeriesService timeSeriesService,
                                  SimpMessagingTemplate messagingTemplate) {
        this.objectMapper = objectMapper;
        this.cacheService = cacheService;
        this.timeSeriesService = timeSeriesService;
        this.messagingTemplate = messagingTemplate;
    }

    /**
     * 실시간 주식 시세 이벤트 처리
     */
    @KafkaListener(
        topics = "kiwoom.realtime.quote",
        groupId = "quantum-web-api-quote",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void handleRealtimeQuote(@Payload RealtimeDataEvent event,
                                   @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
                                   @Header(KafkaHeaders.RECEIVED_PARTITION) int partition,
                                   @Header(KafkaHeaders.OFFSET) long offset,
                                   Acknowledgment acknowledgment) {
        try {
            logger.debug("Received realtime quote event: symbol={}, eventType={}", 
                        event.getSymbol(), event.getEventType());

            // JSON 데이터를 RealtimeQuoteData로 변환
            RealtimeQuoteData quoteData = objectMapper.treeToValue(event.getData(), RealtimeQuoteData.class);
            
            // 필수 필드 설정
            quoteData.setSymbol(event.getSymbol());
            quoteData.setDataType(event.getDataType());
            quoteData.setTimestamp(event.getTimestamp());
            
            // Redis 캐시에 저장 (최신 시세)
            cacheService.cacheQuoteData(event.getSymbol(), quoteData);
            
            // InfluxDB에 시계열 데이터 저장 (비동기)
            timeSeriesService.saveQuoteData(quoteData);
            
            // WebSocket을 통한 실시간 브로드캐스트
            messagingTemplate.convertAndSend("/topic/quote/" + event.getSymbol(), quoteData);
            messagingTemplate.convertAndSend("/topic/quote/all", quoteData);
            
            logger.info("Processed realtime quote: symbol={}, price={}, volume={}", 
                       quoteData.getSymbol(), quoteData.getCurrentPrice(), quoteData.getVolume());

            acknowledgment.acknowledge();

        } catch (JsonProcessingException e) {
            logger.error("Failed to process realtime quote event: {}", event, e);
            acknowledgment.acknowledge(); // 재처리하지 않음 (데이터 포맷 오류)
        } catch (Exception e) {
            logger.error("Unexpected error processing realtime quote: {}", event, e);
            // acknowledgment를 호출하지 않으면 재시도됨
        }
    }

    /**
     * 실시간 주문 체결 이벤트 처리
     */
    @KafkaListener(
        topics = "kiwoom.realtime.order",
        groupId = "quantum-web-api-order",
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void handleRealtimeOrder(@Payload RealtimeDataEvent event,
                                   @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
                                   Acknowledgment acknowledgment) {
        try {
            logger.debug("Received realtime order event: symbol={}, eventType={}", 
                        event.getSymbol(), event.getEventType());

            // JSON 데이터를 RealtimeOrderData로 변환
            RealtimeOrderData orderData = objectMapper.treeToValue(event.getData(), RealtimeOrderData.class);
            
            orderData.setSymbol(event.getSymbol());
            orderData.setTimestamp(event.getTimestamp());
            
            // Redis 캐시에 저장 (계좌별 주문 현황)
            cacheService.cacheOrderData(orderData.getAccountNumber(), orderData);
            
            // InfluxDB에 시계열 데이터 저장 (비동기)
            timeSeriesService.saveOrderData(orderData);
            
            // WebSocket을 통한 실시간 브로드캐스트
            messagingTemplate.convertAndSend("/topic/order/" + orderData.getAccountNumber(), orderData);
            
            logger.info("Processed realtime order: orderId={}, symbol={}, status={}", 
                       orderData.getOrderId(), orderData.getSymbol(), orderData.getOrderStatus());

            acknowledgment.acknowledge();

        } catch (JsonProcessingException e) {
            logger.error("Failed to process realtime order event: {}", event, e);
            acknowledgment.acknowledge();
        } catch (Exception e) {
            logger.error("Unexpected error processing realtime order: {}", event, e);
        }
    }

    /**
     * 실시간 스크리너 이벤트 처리
     */
    @KafkaListener(
        topics = "kiwoom.realtime.screener",
        groupId = "quantum-web-api-screener", 
        containerFactory = "kafkaListenerContainerFactory"
    )
    public void handleRealtimeScreener(@Payload RealtimeDataEvent event,
                                      Acknowledgment acknowledgment) {
        try {
            logger.debug("Received realtime screener event: eventType={}", event.getEventType());

            // JSON 데이터를 RealtimeScreenerData로 변환
            RealtimeScreenerData screenerData = objectMapper.treeToValue(event.getData(), RealtimeScreenerData.class);
            
            screenerData.setTimestamp(event.getTimestamp());
            
            // Redis 캐시에 저장 (조건검색 결과)
            cacheService.cacheScreenerData(screenerData.getConditionName(), screenerData);
            
            // InfluxDB에 시계열 데이터 저장 (비동기)
            timeSeriesService.saveScreenerData(screenerData);
            
            // WebSocket을 통한 실시간 브로드캐스트
            messagingTemplate.convertAndSend("/topic/screener/" + screenerData.getConditionName(), screenerData);
            messagingTemplate.convertAndSend("/topic/screener/all", screenerData);
            
            logger.info("Processed realtime screener: condition={}, symbols count={}", 
                       screenerData.getConditionName(), 
                       screenerData.getSymbols() != null ? screenerData.getSymbols().size() : 0);

            acknowledgment.acknowledge();

        } catch (JsonProcessingException e) {
            logger.error("Failed to process realtime screener event: {}", event, e);
            acknowledgment.acknowledge();
        } catch (Exception e) {
            logger.error("Unexpected error processing realtime screener: {}", event, e);
        }
    }

    /**
     * 일반적인 실시간 이벤트 처리 (fallback)
     */
    @KafkaListener(
        topics = "kiwoom.realtime.general",
        groupId = "quantum-web-api-general",
        containerFactory = "stringKafkaListenerContainerFactory"
    )
    public void handleGeneralEvent(@Payload String eventData,
                                  @Header(KafkaHeaders.RECEIVED_TOPIC) String topic,
                                  Acknowledgment acknowledgment) {
        try {
            logger.debug("Received general event from topic: {}", topic);
            
            // 일반적인 이벤트 데이터를 RealtimeDataEvent로 파싱
            RealtimeDataEvent event = objectMapper.readValue(eventData, RealtimeDataEvent.class);
            
            // WebSocket을 통한 브로드캐스트
            messagingTemplate.convertAndSend("/topic/general", event);
            
            logger.info("Processed general event: type={}, source={}", 
                       event.getEventType(), event.getSource());

            acknowledgment.acknowledge();

        } catch (JsonProcessingException e) {
            logger.error("Failed to process general event: {}", eventData, e);
            acknowledgment.acknowledge();
        } catch (Exception e) {
            logger.error("Unexpected error processing general event: {}", eventData, e);
        }
    }
}