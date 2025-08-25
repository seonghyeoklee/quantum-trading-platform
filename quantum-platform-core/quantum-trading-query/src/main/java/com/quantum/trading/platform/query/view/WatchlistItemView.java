package com.quantum.trading.platform.query.view;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.persistence.*;
import java.time.LocalDateTime;

/**
 * 관심종목 아이템 조회용 View Entity
 * CQRS Query Side Read Model
 */
@Entity
@Table(name = "watchlist_item_view", 
       uniqueConstraints = @UniqueConstraint(columnNames = {"watchlist_id", "symbol"}))
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WatchlistItemView {

    @Id
    @Column(name = "id", length = 36)
    private String id;

    @Column(name = "watchlist_id", length = 36, nullable = false)
    private String watchlistId;

    @Column(name = "group_id", length = 36)
    private String groupId; // nullable - 그룹이 없을 수 있음

    @Column(name = "symbol", length = 20, nullable = false)
    private String symbol;

    @Column(name = "stock_name", length = 100, nullable = false)
    private String stockName;

    @Column(name = "sort_order", nullable = false)
    @Builder.Default
    private Integer sortOrder = 0;

    @Column(name = "note", columnDefinition = "TEXT")
    private String note;

    @Column(name = "added_at", nullable = false)
    private LocalDateTime addedAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Version
    @Column(name = "version")
    @Builder.Default
    private Long version = 0L;

    // ===== 비즈니스 메서드 =====

    public void updateTimestamp() {
        this.updatedAt = LocalDateTime.now();
    }

    public void moveToGroup(String newGroupId) {
        this.groupId = newGroupId;
        updateTimestamp();
    }

    public void removeFromGroup() {
        this.groupId = null;
        updateTimestamp();
    }

    public void updateNote(String newNote) {
        this.note = newNote;
        updateTimestamp();
    }

    public void updateSortOrder(Integer newSortOrder) {
        this.sortOrder = newSortOrder;
        updateTimestamp();
    }

    // ===== 편의 메서드 =====

    public boolean hasGroup() {
        return groupId != null && !groupId.trim().isEmpty();
    }

    public boolean hasNote() {
        return note != null && !note.trim().isEmpty();
    }

    public String getDisplayName() {
        return String.format("%s (%s)", stockName, symbol);
    }

    // ===== equals & hashCode (ID 기반) =====

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof WatchlistItemView)) return false;
        WatchlistItemView that = (WatchlistItemView) o;
        return id != null && id.equals(that.id);
    }

    @Override
    public int hashCode() {
        return id != null ? id.hashCode() : 0;
    }

    @Override
    public String toString() {
        return String.format("WatchlistItemView{id='%s', symbol='%s', stockName='%s', watchlistId='%s'}", 
            id, symbol, stockName, watchlistId);
    }
}