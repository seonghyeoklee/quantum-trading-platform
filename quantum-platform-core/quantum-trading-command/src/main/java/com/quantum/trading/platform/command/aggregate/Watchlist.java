package com.quantum.trading.platform.command.aggregate;

import com.quantum.trading.platform.shared.command.CreateWatchlistCommand;
import com.quantum.trading.platform.shared.command.AddStockToWatchlistCommand;
import com.quantum.trading.platform.shared.command.RemoveStockFromWatchlistCommand;
import com.quantum.trading.platform.shared.command.DeleteWatchlistCommand;
import com.quantum.trading.platform.shared.event.WatchlistCreatedEvent;
import com.quantum.trading.platform.shared.event.StockAddedToWatchlistEvent;
import com.quantum.trading.platform.shared.event.StockRemovedFromWatchlistEvent;
import com.quantum.trading.platform.shared.event.WatchlistDeletedEvent;
import com.quantum.trading.platform.shared.value.Symbol;
import com.quantum.trading.platform.shared.value.UserId;
import com.quantum.trading.platform.shared.value.WatchlistId;
import com.quantum.trading.platform.shared.value.WatchlistGroupId;

import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.axonframework.commandhandling.CommandHandler;
import org.axonframework.eventsourcing.EventSourcingHandler;
import org.axonframework.modelling.command.AggregateIdentifier;
import org.axonframework.modelling.command.AggregateLifecycle;
import org.axonframework.spring.stereotype.Aggregate;

import java.util.HashSet;
import java.util.Set;

/**
 * 관심종목 목록 Aggregate
 * CQRS Command Side 집계루트
 */
@Aggregate
@NoArgsConstructor
@Slf4j
public class Watchlist {

    @AggregateIdentifier
    private WatchlistId watchlistId;
    private UserId userId;
    private String name;
    private String description;
    private boolean isDefault;
    private Set<Symbol> stocks = new HashSet<>();
    private boolean isDeleted = false;

    @CommandHandler
    public Watchlist(CreateWatchlistCommand command) {
        log.info("Creating watchlist with command: {}", command);
        
        // 1. 명령 검증
        command.validate();
        
        // 2. 비즈니스 로직 검증
        validateCreateWatchlist(command);
        
        // 3. 이벤트 발행
        AggregateLifecycle.apply(WatchlistCreatedEvent.of(
            command.getWatchlistId(),
            command.getUserId(),
            command.getName(),
            command.getDescription(),
            command.isDefault()
        ));
    }

    @CommandHandler
    public void handle(AddStockToWatchlistCommand command) {
        log.info("Adding stock to watchlist: {}", command);
        
        // 1. 명령 검증
        command.validate();
        
        // 2. 비즈니스 로직 검증
        validateAddStock(command);
        
        // 3. 이벤트 발행
        AggregateLifecycle.apply(StockAddedToWatchlistEvent.of(
            command.getWatchlistId(),
            command.getUserId(),
            command.getSymbol(),
            command.getStockName(),
            command.getGroupId(),
            command.getNote()
        ));
    }

    @CommandHandler
    public void handle(RemoveStockFromWatchlistCommand command) {
        log.info("Removing stock from watchlist: {}", command);
        
        // 1. 명령 검증
        command.validate();
        
        // 2. 비즈니스 로직 검증
        validateRemoveStock(command);
        
        // 3. 이벤트 발행
        AggregateLifecycle.apply(StockRemovedFromWatchlistEvent.of(
            command.getWatchlistId(),
            command.getUserId(),
            command.getSymbol(),
            getStockName(command.getSymbol()) // 기존에 저장된 종목명 조회 필요
        ));
    }

    @CommandHandler
    public void handle(DeleteWatchlistCommand command) {
        log.info("Deleting watchlist: {}", command);
        
        // 1. 명령 검증
        command.validate();
        
        // 2. 비즈니스 로직 검증
        validateDeleteWatchlist(command);
        
        // 3. 이벤트 발행
        AggregateLifecycle.apply(WatchlistDeletedEvent.of(
            command.getWatchlistId(),
            command.getUserId(),
            this.name
        ));
    }

    // ===== Event Sourcing Handlers =====

    @EventSourcingHandler
    public void on(WatchlistCreatedEvent event) {
        log.debug("Applying WatchlistCreatedEvent: {}", event);
        this.watchlistId = event.getWatchlistId();
        this.userId = event.getUserId();
        this.name = event.getName();
        this.description = event.getDescription();
        this.isDefault = event.isDefault();
        this.stocks = new HashSet<>();
        this.isDeleted = false;
    }

    @EventSourcingHandler
    public void on(StockAddedToWatchlistEvent event) {
        log.debug("Applying StockAddedToWatchlistEvent: {}", event);
        this.stocks.add(event.getSymbol());
    }

    @EventSourcingHandler
    public void on(StockRemovedFromWatchlistEvent event) {
        log.debug("Applying StockRemovedFromWatchlistEvent: {}", event);
        this.stocks.remove(event.getSymbol());
    }

    @EventSourcingHandler
    public void on(WatchlistDeletedEvent event) {
        log.debug("Applying WatchlistDeletedEvent: {}", event);
        this.isDeleted = true;
    }

    // ===== 비즈니스 로직 검증 메서드 =====

    private void validateCreateWatchlist(CreateWatchlistCommand command) {
        // 비즈니스 규칙 검증
        if (command.getName().trim().isEmpty()) {
            throw new IllegalArgumentException("Watchlist name cannot be empty");
        }
    }

    private void validateAddStock(AddStockToWatchlistCommand command) {
        // 집계 상태 검증
        if (isDeleted) {
            throw new IllegalStateException("Cannot add stock to deleted watchlist");
        }
        
        // 권한 검증
        if (!this.userId.equals(command.getUserId())) {
            throw new IllegalStateException("User does not have permission to modify this watchlist");
        }
        
        // 중복 종목 검증
        if (stocks.contains(command.getSymbol())) {
            throw new IllegalArgumentException("Stock already exists in watchlist: " + command.getSymbol());
        }
        
        // 최대 종목 수 제한 (예: 200개)
        if (stocks.size() >= 200) {
            throw new IllegalArgumentException("Watchlist cannot contain more than 200 stocks");
        }
    }

    private void validateRemoveStock(RemoveStockFromWatchlistCommand command) {
        // 집계 상태 검증
        if (isDeleted) {
            throw new IllegalStateException("Cannot remove stock from deleted watchlist");
        }
        
        // 권한 검증
        if (!this.userId.equals(command.getUserId())) {
            throw new IllegalStateException("User does not have permission to modify this watchlist");
        }
        
        // 존재하는 종목인지 검증
        if (!stocks.contains(command.getSymbol())) {
            throw new IllegalArgumentException("Stock does not exist in watchlist: " + command.getSymbol());
        }
    }

    private void validateDeleteWatchlist(DeleteWatchlistCommand command) {
        // 집계 상태 검증
        if (isDeleted) {
            throw new IllegalStateException("Watchlist is already deleted");
        }
        
        // 권한 검증
        if (!this.userId.equals(command.getUserId())) {
            throw new IllegalStateException("User does not have permission to delete this watchlist");
        }
    }

    private String getStockName(Symbol symbol) {
        // 실제로는 종목 정보 조회 서비스에서 가져와야 하지만, 
        // 일단 심볼을 문자열로 반환 (추후 개선)
        return symbol.getValue();
    }

    // ===== Getter 메서드 (테스트용) =====
    
    public WatchlistId getWatchlistId() {
        return watchlistId;
    }
    
    public UserId getUserId() {
        return userId;
    }
    
    public String getName() {
        return name;
    }
    
    public Set<Symbol> getStocks() {
        return new HashSet<>(stocks);
    }
    
    public boolean isDeleted() {
        return isDeleted;
    }
}