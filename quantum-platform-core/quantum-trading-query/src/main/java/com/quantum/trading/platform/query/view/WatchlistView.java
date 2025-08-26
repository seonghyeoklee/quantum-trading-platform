package com.quantum.trading.platform.query.view;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import jakarta.persistence.*;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * 관심종목 목록 조회용 View Entity
 * CQRS Query Side Read Model
 */
@Entity
@Table(name = "watchlist_view")
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class WatchlistView {

    @Id
    @Column(name = "id", length = 36)
    private String id;

    @Column(name = "user_id", length = 36, nullable = false)
    private String userId;

    @Column(name = "name", length = 100, nullable = false)
    private String name;

    @Column(name = "description", columnDefinition = "TEXT")
    private String description;

    @Column(name = "is_default", nullable = false)
    @Builder.Default
    private Boolean isDefault = false;

    @Column(name = "sort_order", nullable = false)
    @Builder.Default
    private Integer sortOrder = 0;

    @Column(name = "item_count", nullable = false)
    @Builder.Default
    private Integer itemCount = 0;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Version
    @Column(name = "version")
    @Builder.Default
    private Long version = 0L;

    // 연관 관계 - 그룹들
    @OneToMany(mappedBy = "watchlistId", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @OrderBy("sortOrder ASC")
    @Builder.Default
    private List<WatchlistGroupView> groups = new ArrayList<>();

    // 연관 관계 - 아이템들
    @OneToMany(mappedBy = "watchlistId", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    @OrderBy("sortOrder ASC")
    @Builder.Default
    private List<WatchlistItemView> items = new ArrayList<>();

    // ===== 비즈니스 메서드 =====

    public void incrementItemCount() {
        this.itemCount = (this.itemCount == null) ? 1 : this.itemCount + 1;
        updateTimestamp();
    }

    public void decrementItemCount() {
        this.itemCount = Math.max(0, (this.itemCount == null) ? 0 : this.itemCount - 1);
        updateTimestamp();
    }

    public void updateTimestamp() {
        this.updatedAt = LocalDateTime.now();
    }

    // ===== 편의 메서드 =====

    public boolean hasItems() {
        return itemCount != null && itemCount > 0;
    }

    public boolean hasGroups() {
        return groups != null && !groups.isEmpty();
    }

    // ===== equals & hashCode (ID 기반) =====

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof WatchlistView)) return false;
        WatchlistView that = (WatchlistView) o;
        return id != null && id.equals(that.id);
    }

    @Override
    public int hashCode() {
        return id != null ? id.hashCode() : 0;
    }

    @Override
    public String toString() {
        return String.format("WatchlistView{id='%s', name='%s', userId='%s', itemCount=%d}", 
            id, name, userId, itemCount);
    }
}