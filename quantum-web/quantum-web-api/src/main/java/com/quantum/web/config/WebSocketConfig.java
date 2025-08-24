package com.quantum.web.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.web.socket.config.annotation.EnableWebSocketMessageBroker;
import org.springframework.web.socket.config.annotation.StompEndpointRegistry;
import org.springframework.web.socket.config.annotation.WebSocketMessageBrokerConfigurer;

/**
 * WebSocket 설정
 * 실시간 데이터 브로드캐스트를 위한 STOMP 메시징 설정
 */
@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    @Override
    public void configureMessageBroker(MessageBrokerRegistry config) {
        // 메시지 브로커 활성화 (클라이언트가 구독하는 경로)
        config.enableSimpleBroker("/topic", "/queue", "/user");
        
        // 클라이언트에서 서버로 메시지를 보낼 때 사용하는 prefix
        config.setApplicationDestinationPrefixes("/app");
        
        // 사용자별 개인 메시지를 위한 prefix
        config.setUserDestinationPrefix("/user");
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        // WebSocket 연결 엔드포인트 등록
        registry.addEndpoint("/ws/realtime")
                .setAllowedOriginPatterns("*")  // 개발용 - 프로덕션에서는 특정 도메인으로 제한
                .withSockJS();  // SockJS fallback 지원
                
        registry.addEndpoint("/ws/realtime")
                .setAllowedOriginPatterns("*");  // 네이티브 WebSocket 지원
    }
}