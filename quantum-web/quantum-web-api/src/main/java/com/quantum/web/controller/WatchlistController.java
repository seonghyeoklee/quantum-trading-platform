package com.quantum.web.controller;

import com.quantum.trading.platform.query.service.WatchlistQueryService;
import com.quantum.trading.platform.query.view.WatchlistView;
import com.quantum.trading.platform.query.view.WatchlistGroupView;
import com.quantum.trading.platform.query.view.WatchlistItemView;
import com.quantum.web.dto.ApiResponse;
import com.quantum.web.security.UserPrincipal;
import com.quantum.web.service.WatchlistService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Watchlist Controller
 *
 * 관심종목 관련 API를 제공하는 컨트롤러
 * - 관심종목 목록 CRUD
 * - 관심종목 그룹 관리
 * - 관심종목 아이템 관리
 */
@Slf4j
@RestController
@RequestMapping("/api/v1/watchlists")
@RequiredArgsConstructor
@Tag(name = "Watchlist", description = "관심종목 관리 API")
public class WatchlistController {

    private final WatchlistService watchlistService;
    private final WatchlistQueryService watchlistQueryService;

    // ===== 관심종목 목록 관리 =====

    @Operation(
        summary = "관심종목 목록 조회",
        description = "사용자의 관심종목 목록을 조회합니다."
    )
    @GetMapping
    public ResponseEntity<ApiResponse<PagedWatchlistResponse>> getWatchlists(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            
            @Parameter(description = "페이지 번호", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "페이지 번호는 0 이상이어야 합니다")
            int page,

            @Parameter(description = "페이지 크기", example = "10")
            @RequestParam(defaultValue = "10")
            @Min(value = 1, message = "페이지 크기는 1 이상이어야 합니다")
            @Max(value = 50, message = "페이지 크기는 50 이하여야 합니다")
            int size
    ) {
        String userId = userPrincipal.getId();
        log.debug("Watchlists requested - userId: {}, page: {}, size: {}", userId, page, size);

        try {
            Pageable pageable = PageRequest.of(page, size);
            Page<WatchlistView> watchlistPage = watchlistQueryService.getUserWatchlists(userId, pageable);

            List<WatchlistDto> watchlists = watchlistPage.getContent().stream()
                    .map(this::convertToWatchlistDto)
                    .collect(Collectors.toList());

            PagedWatchlistResponse response = PagedWatchlistResponse.builder()
                    .content(watchlists)
                    .totalElements(watchlistPage.getTotalElements())
                    .totalPages(watchlistPage.getTotalPages())
                    .number(watchlistPage.getNumber())
                    .size(watchlistPage.getSize())
                    .first(watchlistPage.isFirst())
                    .last(watchlistPage.isLast())
                    .build();

            return ResponseEntity.ok(ApiResponse.success(response,
                "관심종목 목록 조회 완료"));

        } catch (Exception e) {
            log.error("Failed to get watchlists for user: {}", userId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("관심종목 목록 조회 중 오류가 발생했습니다", "WATCHLISTS_GET_ERROR"));
        }
    }

    @Operation(
        summary = "관심종목 목록 생성",
        description = "새로운 관심종목 목록을 생성합니다."
    )
    @PostMapping
    public ResponseEntity<ApiResponse<WatchlistCreatedResponse>> createWatchlist(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            @Valid @RequestBody CreateWatchlistRequest request
    ) {
        String userId = userPrincipal.getId();
        log.debug("Create watchlist requested - userId: {}, name: {}", userId, request.name());

        try {
            String watchlistId = watchlistService.createWatchlist(
                userId, 
                request.name(), 
                request.description(), 
                request.isDefault() != null ? request.isDefault() : false
            );

            WatchlistCreatedResponse response = WatchlistCreatedResponse.builder()
                    .watchlistId(watchlistId)
                    .name(request.name())
                    .description(request.description())
                    .isDefault(request.isDefault() != null ? request.isDefault() : false)
                    .createdAt(LocalDateTime.now())
                    .build();

            log.info("Watchlist created successfully - watchlistId: {}, userId: {}", 
                    watchlistId, userId);

            return ResponseEntity.ok(ApiResponse.success(response,
                "관심종목 목록이 성공적으로 생성되었습니다"));

        } catch (Exception e) {
            log.error("Failed to create watchlist for user: {}", userId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("관심종목 목록 생성 중 오류가 발생했습니다", "WATCHLIST_CREATE_ERROR"));
        }
    }

    @Operation(
        summary = "관심종목 목록 상세 조회",
        description = "특정 관심종목 목록의 상세 정보를 조회합니다."
    )
    @GetMapping("/{watchlistId}")
    public ResponseEntity<ApiResponse<WatchlistDetailDto>> getWatchlist(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            
            @Parameter(description = "관심종목 목록 ID", example = "WATCHLIST-123")
            @PathVariable String watchlistId
    ) {
        String userId = userPrincipal.getId();
        log.debug("Watchlist detail requested - watchlistId: {}, userId: {}", watchlistId, userId);

        try {
            var watchlist = watchlistQueryService.getWatchlistById(watchlistId, userId)
                    .orElse(null);

            if (watchlist == null) {
                return ResponseEntity.notFound().build();
            }

            // 관심종목 그룹들 조회
            List<WatchlistGroupView> groups = watchlistQueryService.getWatchlistGroups(watchlistId);
            List<WatchlistGroupDto> groupDtos = groups.stream()
                    .map(this::convertToWatchlistGroupDto)
                    .collect(Collectors.toList());

            // 관심종목 아이템들 조회
            List<WatchlistItemView> items = watchlistQueryService.getWatchlistItems(watchlistId);
            List<WatchlistItemDto> itemDtos = items.stream()
                    .map(this::convertToWatchlistItemDto)
                    .collect(Collectors.toList());

            WatchlistDetailDto response = WatchlistDetailDto.builder()
                    .id(watchlist.getId())
                    .userId(watchlist.getUserId())
                    .name(watchlist.getName())
                    .description(watchlist.getDescription())
                    .isDefault(watchlist.getIsDefault())
                    .sortOrder(watchlist.getSortOrder())
                    .itemCount(watchlist.getItemCount())
                    .groups(groupDtos)
                    .items(itemDtos)
                    .createdAt(watchlist.getCreatedAt())
                    .updatedAt(watchlist.getUpdatedAt())
                    .build();

            return ResponseEntity.ok(ApiResponse.success(response,
                String.format("관심종목 목록 상세 조회 완료 - %s", watchlistId)));

        } catch (Exception e) {
            log.error("Failed to get watchlist: {}", watchlistId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("관심종목 목록 조회 중 오류가 발생했습니다", "WATCHLIST_GET_ERROR"));
        }
    }

    @Operation(
        summary = "관심종목 목록 삭제",
        description = "관심종목 목록을 삭제합니다."
    )
    @DeleteMapping("/{watchlistId}")
    public ResponseEntity<ApiResponse<String>> deleteWatchlist(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            
            @Parameter(description = "관심종목 목록 ID", example = "WATCHLIST-123")
            @PathVariable String watchlistId
    ) {
        String userId = userPrincipal.getId();
        log.debug("Delete watchlist requested - watchlistId: {}, userId: {}", watchlistId, userId);

        try {
            watchlistService.deleteWatchlist(watchlistId, userId);

            log.info("Watchlist deleted successfully - watchlistId: {}, userId: {}", watchlistId, userId);

            return ResponseEntity.ok(ApiResponse.success("관심종목 목록이 성공적으로 삭제되었습니다",
                "관심종목 목록 삭제 완료"));

        } catch (Exception e) {
            log.error("Failed to delete watchlist: {}", watchlistId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("관심종목 목록 삭제 중 오류가 발생했습니다", "WATCHLIST_DELETE_ERROR"));
        }
    }

    // ===== 관심종목 아이템 관리 =====

    @Operation(
        summary = "관심종목에 종목 추가",
        description = "관심종목 목록에 종목을 추가합니다."
    )
    @PostMapping("/{watchlistId}/stocks")
    public ResponseEntity<ApiResponse<StockAddedResponse>> addStockToWatchlist(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            
            @Parameter(description = "관심종목 목록 ID", example = "WATCHLIST-123")
            @PathVariable String watchlistId,
            
            @Valid @RequestBody AddStockRequest request
    ) {
        String userId = userPrincipal.getId();
        log.debug("Add stock requested - watchlistId: {}, symbol: {}, userId: {}", 
                watchlistId, request.symbol(), userId);

        try {
            watchlistService.addStockToWatchlist(
                watchlistId, 
                userId, 
                request.groupId(), 
                request.symbol(), 
                request.stockName(), 
                request.note()
            );

            StockAddedResponse response = StockAddedResponse.builder()
                    .watchlistId(watchlistId)
                    .symbol(request.symbol())
                    .stockName(request.stockName())
                    .groupId(request.groupId())
                    .note(request.note())
                    .addedAt(LocalDateTime.now())
                    .build();

            log.info("Stock added to watchlist successfully - watchlistId: {}, symbol: {}, userId: {}", 
                    watchlistId, request.symbol(), userId);

            return ResponseEntity.ok(ApiResponse.success(response,
                "종목이 성공적으로 관심종목에 추가되었습니다"));

        } catch (Exception e) {
            log.error("Failed to add stock to watchlist - watchlistId: {}, symbol: {}", 
                    watchlistId, request.symbol(), e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("관심종목 추가 중 오류가 발생했습니다", "STOCK_ADD_ERROR"));
        }
    }

    @Operation(
        summary = "관심종목에서 종목 제거",
        description = "관심종목 목록에서 종목을 제거합니다."
    )
    @DeleteMapping("/{watchlistId}/stocks/{symbol}")
    public ResponseEntity<ApiResponse<String>> removeStockFromWatchlist(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            
            @Parameter(description = "관심종목 목록 ID", example = "WATCHLIST-123")
            @PathVariable String watchlistId,
            
            @Parameter(description = "종목 코드", example = "005930")
            @PathVariable String symbol
    ) {
        String userId = userPrincipal.getId();
        log.debug("Remove stock requested - watchlistId: {}, symbol: {}, userId: {}", 
                watchlistId, symbol, userId);

        try {
            watchlistService.removeStockFromWatchlist(watchlistId, userId, symbol);

            log.info("Stock removed from watchlist successfully - watchlistId: {}, symbol: {}, userId: {}", 
                    watchlistId, symbol, userId);

            return ResponseEntity.ok(ApiResponse.success("종목이 성공적으로 관심종목에서 제거되었습니다",
                "관심종목 제거 완료"));

        } catch (Exception e) {
            log.error("Failed to remove stock from watchlist - watchlistId: {}, symbol: {}", 
                    watchlistId, symbol, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("관심종목 제거 중 오류가 발생했습니다", "STOCK_REMOVE_ERROR"));
        }
    }

    @Operation(
        summary = "관심종목 아이템 검색",
        description = "관심종목 목록에서 종목을 검색합니다."
    )
    @GetMapping("/{watchlistId}/stocks/search")
    public ResponseEntity<ApiResponse<List<WatchlistItemDto>>> searchWatchlistItems(
            @AuthenticationPrincipal UserPrincipal userPrincipal,
            
            @Parameter(description = "관심종목 목록 ID", example = "WATCHLIST-123")
            @PathVariable String watchlistId,
            
            @Parameter(description = "검색어", example = "삼성")
            @RequestParam
            @NotBlank(message = "검색어를 입력해주세요")
            String query
    ) {
        String userId = userPrincipal.getId();
        log.debug("Search watchlist items requested - watchlistId: {}, query: {}, userId: {}", 
                watchlistId, query, userId);

        try {
            // 권한 확인
            if (!watchlistQueryService.isWatchlistOwner(watchlistId, userId)) {
                return ResponseEntity.badRequest()
                        .body(ApiResponse.error("관심종목 목록에 접근할 권한이 없습니다", "WATCHLIST_ACCESS_FORBIDDEN"));
            }

            List<WatchlistItemView> items = watchlistQueryService.searchWatchlistItems(watchlistId, query);
            
            List<WatchlistItemDto> itemDtos = items.stream()
                    .map(this::convertToWatchlistItemDto)
                    .collect(Collectors.toList());

            return ResponseEntity.ok(ApiResponse.success(itemDtos,
                String.format("관심종목 검색 완료 - %d개 결과", itemDtos.size())));

        } catch (Exception e) {
            log.error("Failed to search watchlist items - watchlistId: {}, query: {}", 
                    watchlistId, query, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("관심종목 검색 중 오류가 발생했습니다", "WATCHLIST_SEARCH_ERROR"));
        }
    }

    @Operation(
        summary = "사용자 통계 조회",
        description = "사용자의 관심종목 통계를 조회합니다."
    )
    @GetMapping("/stats")
    public ResponseEntity<ApiResponse<UserWatchlistStatsDto>> getUserStats(
            @AuthenticationPrincipal UserPrincipal userPrincipal
    ) {
        String userId = userPrincipal.getId();
        log.debug("User watchlist stats requested - userId: {}", userId);

        try {
            WatchlistQueryService.UserWatchlistStats stats = watchlistQueryService.getUserWatchlistStats(userId);
            
            UserWatchlistStatsDto statsDto = UserWatchlistStatsDto.builder()
                    .userId(stats.getUserId())
                    .watchlistCount(stats.getWatchlistCount())
                    .totalItemCount(stats.getTotalItemCount())
                    .hasDefaultWatchlist(stats.isHasDefaultWatchlist())
                    .build();

            return ResponseEntity.ok(ApiResponse.success(statsDto,
                "사용자 관심종목 통계 조회 완료"));

        } catch (Exception e) {
            log.error("Failed to get user watchlist stats for user: {}", userId, e);
            return ResponseEntity.internalServerError()
                    .body(ApiResponse.error("통계 조회 중 오류가 발생했습니다", "STATS_GET_ERROR"));
        }
    }

    // ===== Helper Methods =====

    private WatchlistDto convertToWatchlistDto(WatchlistView watchlist) {
        return WatchlistDto.builder()
                .id(watchlist.getId())
                .userId(watchlist.getUserId())
                .name(watchlist.getName())
                .description(watchlist.getDescription())
                .isDefault(watchlist.getIsDefault())
                .sortOrder(watchlist.getSortOrder())
                .itemCount(watchlist.getItemCount())
                .createdAt(watchlist.getCreatedAt())
                .updatedAt(watchlist.getUpdatedAt())
                .build();
    }

    private WatchlistGroupDto convertToWatchlistGroupDto(WatchlistGroupView group) {
        return WatchlistGroupDto.builder()
                .id(group.getId())
                .watchlistId(group.getWatchlistId())
                .name(group.getName())
                .color(group.getColor())
                .sortOrder(group.getSortOrder())
                .itemCount(group.getItemCount())
                .createdAt(group.getCreatedAt())
                .updatedAt(group.getUpdatedAt())
                .build();
    }

    private WatchlistItemDto convertToWatchlistItemDto(WatchlistItemView item) {
        return WatchlistItemDto.builder()
                .id(item.getId())
                .watchlistId(item.getWatchlistId())
                .groupId(item.getGroupId())
                .symbol(item.getSymbol())
                .stockName(item.getStockName())
                .sortOrder(item.getSortOrder())
                .note(item.getNote())
                .addedAt(item.getAddedAt())
                .updatedAt(item.getUpdatedAt())
                .build();
    }

    // ===== Request/Response DTOs =====

    public record CreateWatchlistRequest(
            @NotBlank(message = "관심종목 목록명을 입력해주세요")
            @Size(max = 100, message = "관심종목 목록명은 100자 이내여야 합니다")
            String name,

            @Size(max = 500, message = "설명은 500자 이내여야 합니다")
            String description,

            Boolean isDefault
    ) {}

    public record AddStockRequest(
            @NotBlank(message = "종목 코드를 입력해주세요")
            @Pattern(regexp = "^[0-9]{6}$", message = "종목 코드는 6자리 숫자여야 합니다")
            String symbol,

            @NotBlank(message = "종목명을 입력해주세요")
            @Size(max = 100, message = "종목명은 100자 이내여야 합니다")
            String stockName,

            String groupId,

            @Size(max = 500, message = "메모는 500자 이내여야 합니다")
            String note
    ) {}

    @lombok.Builder
    public record WatchlistCreatedResponse(
            String watchlistId,
            String name,
            String description,
            boolean isDefault,
            LocalDateTime createdAt
    ) {}

    @lombok.Builder
    public record StockAddedResponse(
            String watchlistId,
            String symbol,
            String stockName,
            String groupId,
            String note,
            LocalDateTime addedAt
    ) {}

    @lombok.Builder
    public record WatchlistDto(
            String id,
            String userId,
            String name,
            String description,
            boolean isDefault,
            int sortOrder,
            int itemCount,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {}

    @lombok.Builder
    public record WatchlistDetailDto(
            String id,
            String userId,
            String name,
            String description,
            boolean isDefault,
            int sortOrder,
            int itemCount,
            List<WatchlistGroupDto> groups,
            List<WatchlistItemDto> items,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {}

    @lombok.Builder
    public record WatchlistGroupDto(
            String id,
            String watchlistId,
            String name,
            String color,
            int sortOrder,
            int itemCount,
            LocalDateTime createdAt,
            LocalDateTime updatedAt
    ) {}

    @lombok.Builder
    public record WatchlistItemDto(
            String id,
            String watchlistId,
            String groupId,
            String symbol,
            String stockName,
            int sortOrder,
            String note,
            LocalDateTime addedAt,
            LocalDateTime updatedAt
    ) {}

    @lombok.Builder
    public record PagedWatchlistResponse(
            List<WatchlistDto> content,
            long totalElements,
            int totalPages,
            int number,
            int size,
            boolean first,
            boolean last
    ) {}

    @lombok.Builder
    public record UserWatchlistStatsDto(
            String userId,
            long watchlistCount,
            long totalItemCount,
            boolean hasDefaultWatchlist
    ) {}
}