package com.quantum.trading.platform.query.projection;

import com.quantum.trading.platform.query.repository.PortfolioViewRepository;
import com.quantum.trading.platform.query.view.PortfolioView;
import com.quantum.trading.platform.query.view.PositionView;
import com.quantum.trading.platform.shared.event.*;
import com.quantum.trading.platform.shared.value.Position;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.axonframework.eventhandling.EventHandler;
import org.springframework.stereotype.Component;

/**
 * 포트폴리오 이벤트를 구독하여 PortfolioView를 업데이트하는 Projection Handler
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class PortfolioProjectionHandler {
    
    private final PortfolioViewRepository portfolioViewRepository;
    
    /**
     * 포트폴리오 생성 이벤트 처리
     */
    @EventHandler
    public void on(PortfolioCreatedEvent event) {
        log.info("Processing PortfolioCreatedEvent: {}", event.getPortfolioId());
        
        PortfolioView portfolioView = PortfolioView.fromPortfolioCreated(
                event.getPortfolioId(),
                event.getUserId(),
                event.getInitialCash(),
                event.getTimestamp()
        );
        
        portfolioViewRepository.save(portfolioView);
        
        log.debug("PortfolioView created: {}", portfolioView.getPortfolioId());
    }
    
    /**
     * 현금 입금 이벤트 처리
     */
    @EventHandler
    public void on(CashDepositedEvent event) {
        log.info("Processing CashDepositedEvent: {} - {}", 
                event.portfolioId(), event.amount());
        
        portfolioViewRepository.findById(event.portfolioId().id())
                .ifPresentOrElse(
                        portfolioView -> {
                            portfolioView.updateCashBalance(
                                    event.newCashBalance().amount(),
                                    event.timestamp()
                            );
                            portfolioViewRepository.save(portfolioView);
                            log.debug("PortfolioView cash updated: {} -> {}", 
                                    event.portfolioId(), event.newCashBalance());
                        },
                        () -> log.warn("PortfolioView not found for cash deposit: {}", event.portfolioId())
                );
    }
    
    /**
     * 포지션 업데이트 이벤트 처리
     */
    @EventHandler
    public void on(PositionUpdatedEvent event) {
        log.info("Processing PositionUpdatedEvent: {} - {} {} @ {}", 
                event.portfolioId(), event.side(), event.symbol(), event.price());
        
        portfolioViewRepository.findById(event.portfolioId().id())
                .ifPresentOrElse(
                        portfolioView -> {
                            // Position 도메인 객체에서 PositionView로 변환
                            Position position = event.newPosition();
                            PositionView positionView = PositionView.fromPosition(position, event.timestamp());
                            
                            // 현금 잔액 업데이트
                            portfolioView.updateCashBalance(
                                    event.newCashBalance().amount(),
                                    event.timestamp()
                            );
                            
                            // 포지션 업데이트
                            portfolioView.updatePosition(positionView, event.timestamp());
                            
                            portfolioViewRepository.save(portfolioView);
                            
                            log.debug("PortfolioView position updated: {} {} - {} shares", 
                                    event.portfolioId(), event.symbol(), position.getQuantity().value());
                        },
                        () -> log.warn("PortfolioView not found for position update: {}", event.portfolioId())
                );
    }
    
    /**
     * 주문 체결 이벤트 처리 (포트폴리오 메트릭 업데이트용)
     */
    @EventHandler
    public void on(OrderExecutedEvent event) {
        log.debug("Processing OrderExecutedEvent for portfolio metrics update: {}", event.getOrderId());
        
        // 주문 체결 시 포트폴리오의 메트릭을 재계산
        // 이는 PositionUpdatedEvent와 연동되어 처리됨
        // 필요에 따라 추가적인 메트릭 업데이트 로직을 여기에 구현
    }
}