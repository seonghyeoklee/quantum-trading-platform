package com.quantum.web.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.quantum.web.events.RealtimeOrderData;
import com.quantum.web.events.RealtimeQuoteData;
import com.quantum.web.events.RealtimeScreenerData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.List;
import java.util.Set;

/**
 * 실시간 데이터 Redis 캐싱 서비스
 * 실시간 주식 시세, 주문 체결, 스크리너 데이터를 캐싱하여 빠른 조회 지원
 */
@Service
public class RealtimeDataCacheService {

    private static final Logger logger = LoggerFactory.getLogger(RealtimeDataCacheService.class);

    private final RedisTemplate<String, Object> redisTemplate;
    private final ObjectMapper objectMapper;

    // Cache Keys
    private static final String QUOTE_KEY_PREFIX = "realtime:quote:";
    private static final String ORDER_KEY_PREFIX = "realtime:order:";
    private static final String SCREENER_KEY_PREFIX = "realtime:screener:";
    private static final String QUOTE_LIST_KEY = "realtime:quotes:all";

    // Cache TTL
    private static final Duration QUOTE_TTL = Duration.ofMinutes(5);  // 시세 데이터 5분
    private static final Duration ORDER_TTL = Duration.ofHours(1);    // 주문 데이터 1시간
    private static final Duration SCREENER_TTL = Duration.ofMinutes(30); // 스크리너 30분

    public RealtimeDataCacheService(RedisTemplate<String, Object> redisTemplate, ObjectMapper objectMapper) {
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    /**
     * 실시간 주식 시세 데이터 캐싱
     */
    public void cacheQuoteData(String symbol, RealtimeQuoteData quoteData) {
        try {
            String key = QUOTE_KEY_PREFIX + symbol;
            
            // 개별 종목 시세 저장
            redisTemplate.opsForValue().set(key, quoteData, QUOTE_TTL);
            
            // 전체 종목 목록에 추가 (최근 업데이트된 종목 추적용)
            redisTemplate.opsForSet().add(QUOTE_LIST_KEY, symbol);
            redisTemplate.expire(QUOTE_LIST_KEY, QUOTE_TTL);
            
            logger.debug("Cached quote data for symbol: {}", symbol);
            
        } catch (Exception e) {
            logger.error("Failed to cache quote data for symbol: {}", symbol, e);
        }
    }

    /**
     * 실시간 주식 시세 조회
     */
    public RealtimeQuoteData getQuoteData(String symbol) {
        try {
            String key = QUOTE_KEY_PREFIX + symbol;
            Object cached = redisTemplate.opsForValue().get(key);
            
            if (cached != null) {
                return objectMapper.convertValue(cached, RealtimeQuoteData.class);
            }
            
            return null;
            
        } catch (Exception e) {
            logger.error("Failed to get quote data for symbol: {}", symbol, e);
            return null;
        }
    }

    /**
     * 실시간 주문 데이터 캐싱
     */
    public void cacheOrderData(String accountNumber, RealtimeOrderData orderData) {
        try {
            String key = ORDER_KEY_PREFIX + accountNumber + ":" + orderData.getOrderId();
            
            redisTemplate.opsForValue().set(key, orderData, ORDER_TTL);
            
            // 계좌별 주문 목록에 추가
            String accountOrdersKey = ORDER_KEY_PREFIX + "account:" + accountNumber;
            redisTemplate.opsForSet().add(accountOrdersKey, orderData.getOrderId());
            redisTemplate.expire(accountOrdersKey, ORDER_TTL);
            
            logger.debug("Cached order data: account={}, orderId={}", accountNumber, orderData.getOrderId());
            
        } catch (Exception e) {
            logger.error("Failed to cache order data: account={}, orderId={}", accountNumber, orderData.getOrderId(), e);
        }
    }

    /**
     * 계좌별 주문 데이터 조회
     */
    public List<RealtimeOrderData> getOrderDataByAccount(String accountNumber) {
        try {
            String accountOrdersKey = ORDER_KEY_PREFIX + "account:" + accountNumber;
            Set<Object> orderIds = redisTemplate.opsForSet().members(accountOrdersKey);
            
            if (orderIds == null || orderIds.isEmpty()) {
                return List.of();
            }
            
            return orderIds.stream()
                    .map(orderId -> {
                        String key = ORDER_KEY_PREFIX + accountNumber + ":" + orderId;
                        Object cached = redisTemplate.opsForValue().get(key);
                        if (cached != null) {
                            return objectMapper.convertValue(cached, RealtimeOrderData.class);
                        }
                        return null;
                    })
                    .filter(order -> order != null)
                    .toList();
            
        } catch (Exception e) {
            logger.error("Failed to get order data for account: {}", accountNumber, e);
            return List.of();
        }
    }

    /**
     * 실시간 스크리너 데이터 캐싱
     */
    public void cacheScreenerData(String conditionName, RealtimeScreenerData screenerData) {
        try {
            String key = SCREENER_KEY_PREFIX + conditionName;
            
            redisTemplate.opsForValue().set(key, screenerData, SCREENER_TTL);
            
            logger.debug("Cached screener data for condition: {}", conditionName);
            
        } catch (Exception e) {
            logger.error("Failed to cache screener data for condition: {}", conditionName, e);
        }
    }

    /**
     * 스크리너 데이터 조회
     */
    public RealtimeScreenerData getScreenerData(String conditionName) {
        try {
            String key = SCREENER_KEY_PREFIX + conditionName;
            Object cached = redisTemplate.opsForValue().get(key);
            
            if (cached != null) {
                return objectMapper.convertValue(cached, RealtimeScreenerData.class);
            }
            
            return null;
            
        } catch (Exception e) {
            logger.error("Failed to get screener data for condition: {}", conditionName, e);
            return null;
        }
    }

    /**
     * 캐시된 모든 종목 시세 조회
     */
    public List<RealtimeQuoteData> getAllQuoteData() {
        try {
            Set<Object> symbols = redisTemplate.opsForSet().members(QUOTE_LIST_KEY);
            
            if (symbols == null || symbols.isEmpty()) {
                return List.of();
            }
            
            return symbols.stream()
                    .map(symbol -> getQuoteData(symbol.toString()))
                    .filter(quote -> quote != null)
                    .toList();
            
        } catch (Exception e) {
            logger.error("Failed to get all quote data", e);
            return List.of();
        }
    }

    /**
     * 특정 키 패턴의 캐시 삭제
     */
    public void evictCache(String keyPattern) {
        try {
            Set<String> keys = redisTemplate.keys(keyPattern);
            if (keys != null && !keys.isEmpty()) {
                redisTemplate.delete(keys);
                logger.info("Evicted {} cache entries with pattern: {}", keys.size(), keyPattern);
            }
        } catch (Exception e) {
            logger.error("Failed to evict cache with pattern: {}", keyPattern, e);
        }
    }

    /**
     * 모든 실시간 데이터 캐시 삭제
     */
    public void evictAllRealtimeCache() {
        evictCache("realtime:*");
    }
}