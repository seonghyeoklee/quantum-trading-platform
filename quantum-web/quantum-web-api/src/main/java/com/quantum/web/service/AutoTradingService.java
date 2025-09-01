package com.quantum.web.service;

import com.quantum.web.dto.AutoTradingConfigDto;
import com.quantum.web.dto.AutoTradingStatusDto;
import com.quantum.web.entity.AutoTradingConfig;
import com.quantum.web.entity.AutoTradingStatus;
import com.quantum.web.repository.AutoTradingConfigRepository;
import com.quantum.web.repository.AutoTradingStatusRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * 자동매매 서비스
 *
 * 자동매매 설정 및 상태 관리를 담당하는 서비스
 * - 자동매매 설정 CRUD 작업
 * - 자동매매 시작/정지/일시정지/재개 제어
 * - 실시간 상태 모니터링 및 성과 추적
 */
@Slf4j
@Service
@RequiredArgsConstructor
@Transactional
public class AutoTradingService {

    private final AutoTradingConfigRepository autoTradingConfigRepository;
    private final AutoTradingStatusRepository autoTradingStatusRepository;
    private final TradingSignalService tradingSignalService;

    /**
     * 자동매매 설정 생성
     *
     * @param request 자동매매 설정 생성 요청
     * @return 생성된 자동매매 설정 응답
     */
    public AutoTradingConfigDto.Response createConfig(AutoTradingConfigDto.CreateRequest request) {
        log.info("Creating auto trading config - strategy: {}, symbol: {}, capital: {}",
                request.strategyName(), request.symbol(), request.capital());

        // 1. 중복 설정 검증
        validateDuplicateConfig(request.strategyName(), request.symbol());

        // 2. 설정 유효성 검증
        validateConfigRequest(request);

        // 3. AutoTradingConfig 엔티티 생성
        AutoTradingConfig config = AutoTradingConfig.builder()
                .id(generateConfigId())
                .strategyName(request.strategyName())
                .symbol(request.symbol())
                .capital(request.capital())
                .maxPositionSize(request.maxPositionSize())
                .stopLossPercent(request.stopLossPercent())
                .takeProfitPercent(request.takeProfitPercent())
                .isActive(true) // 기본값으로 활성화
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        // 4. 데이터베이스 저장
        AutoTradingConfig savedConfig = autoTradingConfigRepository.save(config);

        // 5. 초기 상태 생성
        createInitialStatus(savedConfig);

        log.info("Auto trading config created successfully - id: {}", savedConfig.getId());

        // 6. 응답 DTO 변환
        return convertToConfigResponse(savedConfig);
    }

    /**
     * 자동매매 설정 목록 조회
     *
     * @param userId 사용자 ID
     * @param isActive 활성 상태 필터
     * @return 자동매매 설정 목록
     */
    @Transactional(readOnly = true)
    public List<AutoTradingConfigDto.Response> getConfigs(String userId, Boolean isActive) {
        log.debug("Getting auto trading configs - userId: {}, isActive: {}", userId, isActive);

        List<AutoTradingConfig> configs;

        if (isActive != null) {
            configs = autoTradingConfigRepository.findByIsActive(isActive);
        } else {
            configs = autoTradingConfigRepository.findAll();
        }

        return configs.stream()
                .map(this::convertToConfigResponse)
                .toList();
    }

    /**
     * 자동매매 설정 상세 조회
     *
     * @param configId 설정 ID
     * @return 자동매매 설정 상세 정보
     */
    @Transactional(readOnly = true)
    public AutoTradingConfigDto.Response getConfig(String configId) {
        log.debug("Getting auto trading config - configId: {}", configId);

        Optional<AutoTradingConfig> configOpt = autoTradingConfigRepository.findById(configId);
        
        if (configOpt.isEmpty()) {
            return null;
        }

        return convertToConfigResponse(configOpt.get());
    }

    /**
     * 자동매매 상태 조회
     *
     * @param configId 설정 ID
     * @return 자동매매 상태 정보
     */
    @Transactional(readOnly = true)
    public AutoTradingStatusDto.Response getStatus(String configId) {
        log.debug("Getting auto trading status - configId: {}", configId);

        Optional<AutoTradingStatus> statusOpt = autoTradingStatusRepository.findByConfigId(configId);
        
        if (statusOpt.isEmpty()) {
            return null;
        }

        return convertToStatusResponse(statusOpt.get());
    }

    /**
     * 자동매매 시작
     *
     * @param configId 설정 ID
     */
    public void startTrading(String configId) {
        log.info("Starting auto trading - configId: {}", configId);

        // 1. 설정 조회 및 검증
        AutoTradingConfig config = autoTradingConfigRepository.findById(configId)
                .orElseThrow(() -> new IllegalArgumentException("설정을 찾을 수 없습니다: " + configId));

        if (!config.getIsActive()) {
            throw new IllegalArgumentException("비활성화된 설정입니다");
        }

        // 2. 상태 업데이트
        AutoTradingStatus status = autoTradingStatusRepository.findByConfigId(configId)
                .orElseThrow(() -> new IllegalArgumentException("상태를 찾을 수 없습니다: " + configId));

        if ("running".equals(status.getStatus())) {
            throw new IllegalArgumentException("이미 실행 중인 자동매매입니다");
        }

        status.setStatus("running");
        status.setStartedAt(LocalDateTime.now());
        status.setUpdatedAt(LocalDateTime.now());

        autoTradingStatusRepository.save(status);

        // 3. 전략 활성화 (TradingSignalService 연동)
        tradingSignalService.setStrategyEnabled(config.getStrategyName(), true);

        log.info("Auto trading started successfully - configId: {}", configId);
    }

    /**
     * 자동매매 정지
     *
     * @param configId 설정 ID
     */
    public void stopTrading(String configId) {
        log.info("Stopping auto trading - configId: {}", configId);

        // 1. 설정 조회
        AutoTradingConfig config = autoTradingConfigRepository.findById(configId)
                .orElseThrow(() -> new IllegalArgumentException("설정을 찾을 수 없습니다: " + configId));

        // 2. 상태 업데이트
        AutoTradingStatus status = autoTradingStatusRepository.findByConfigId(configId)
                .orElseThrow(() -> new IllegalArgumentException("상태를 찾을 수 없습니다: " + configId));

        status.setStatus("stopped");
        status.setStoppedAt(LocalDateTime.now());
        status.setUpdatedAt(LocalDateTime.now());

        autoTradingStatusRepository.save(status);

        // 3. 전략 비활성화 (TradingSignalService 연동)
        tradingSignalService.setStrategyEnabled(config.getStrategyName(), false);

        log.info("Auto trading stopped successfully - configId: {}", configId);
    }

    /**
     * 자동매매 일시정지
     *
     * @param configId 설정 ID
     */
    public void pauseTrading(String configId) {
        log.info("Pausing auto trading - configId: {}", configId);

        // 상태 업데이트
        AutoTradingStatus status = autoTradingStatusRepository.findByConfigId(configId)
                .orElseThrow(() -> new IllegalArgumentException("상태를 찾을 수 없습니다: " + configId));

        if (!"running".equals(status.getStatus())) {
            throw new IllegalArgumentException("실행 중인 자동매매가 아닙니다");
        }

        status.setStatus("paused");
        status.setUpdatedAt(LocalDateTime.now());

        autoTradingStatusRepository.save(status);

        log.info("Auto trading paused successfully - configId: {}", configId);
    }

    /**
     * 자동매매 재개
     *
     * @param configId 설정 ID
     */
    public void resumeTrading(String configId) {
        log.info("Resuming auto trading - configId: {}", configId);

        // 상태 업데이트
        AutoTradingStatus status = autoTradingStatusRepository.findByConfigId(configId)
                .orElseThrow(() -> new IllegalArgumentException("상태를 찾을 수 없습니다: " + configId));

        if (!"paused".equals(status.getStatus())) {
            throw new IllegalArgumentException("일시정지된 자동매매가 아닙니다");
        }

        status.setStatus("running");
        status.setUpdatedAt(LocalDateTime.now());

        autoTradingStatusRepository.save(status);

        log.info("Auto trading resumed successfully - configId: {}", configId);
    }

    /**
     * 자동매매 설정 삭제
     *
     * @param configId 설정 ID
     */
    public void deleteConfig(String configId) {
        log.info("Deleting auto trading config - configId: {}", configId);

        // 1. 설정 조회
        AutoTradingConfig config = autoTradingConfigRepository.findById(configId)
                .orElseThrow(() -> new IllegalArgumentException("설정을 찾을 수 없습니다: " + configId));

        // 2. 실행 중인 경우 먼저 정지
        AutoTradingStatus status = autoTradingStatusRepository.findByConfigId(configId)
                .orElse(null);

        if (status != null && "running".equals(status.getStatus())) {
            stopTrading(configId);
        }

        // 3. 관련 상태 삭제
        if (status != null) {
            autoTradingStatusRepository.delete(status);
        }

        // 4. 설정 삭제
        autoTradingConfigRepository.delete(config);

        log.info("Auto trading config deleted successfully - configId: {}", configId);
    }

    /**
     * 중복 설정 검증
     */
    private void validateDuplicateConfig(String strategyName, String symbol) {
        boolean exists = autoTradingConfigRepository.existsByStrategyNameAndSymbolAndIsActive(
                strategyName, symbol, true);

        if (exists) {
            throw new IllegalArgumentException(
                    String.format("이미 활성화된 자동매매 설정이 있습니다 - 전략: %s, 종목: %s", 
                            strategyName, symbol));
        }
    }

    /**
     * 설정 요청 유효성 검증
     */
    private void validateConfigRequest(AutoTradingConfigDto.CreateRequest request) {
        // 1. 기본 필드 검증
        if (request.strategyName() == null || request.strategyName().trim().isEmpty()) {
            throw new IllegalArgumentException("전략명은 필수입니다");
        }

        if (request.symbol() == null || !request.symbol().matches("^[A-Z0-9]{6}$")) {
            throw new IllegalArgumentException("유효하지 않은 종목 코드입니다");
        }

        if (request.capital() == null || request.capital().compareTo(BigDecimal.ZERO) <= 0) {
            throw new IllegalArgumentException("투자 금액은 0보다 커야 합니다");
        }

        // 2. 퍼센트 값 검증
        if (request.maxPositionSize() == null || request.maxPositionSize() <= 0 || request.maxPositionSize() > 100) {
            throw new IllegalArgumentException("최대 포지션 크기는 1-100% 사이여야 합니다");
        }

        if (request.stopLossPercent() == null || 
            request.stopLossPercent().compareTo(BigDecimal.ZERO) <= 0 || 
            request.stopLossPercent().compareTo(BigDecimal.valueOf(50)) >= 0) {
            throw new IllegalArgumentException("손절 비율은 0-50% 사이여야 합니다");
        }

        if (request.takeProfitPercent() == null || 
            request.takeProfitPercent().compareTo(BigDecimal.ZERO) <= 0 || 
            request.takeProfitPercent().compareTo(BigDecimal.valueOf(100)) >= 0) {
            throw new IllegalArgumentException("익절 비율은 0-100% 사이여야 합니다");
        }

        // 3. 손절/익절 비율 관계 검증
        if (request.stopLossPercent().compareTo(request.takeProfitPercent()) >= 0) {
            throw new IllegalArgumentException("익절 비율은 손절 비율보다 커야 합니다");
        }

        log.debug("Config request validation passed - strategy: {}, symbol: {}", 
                request.strategyName(), request.symbol());
    }

    /**
     * 초기 상태 생성
     */
    private void createInitialStatus(AutoTradingConfig config) {
        AutoTradingStatus status = AutoTradingStatus.builder()
                .id(generateStatusId())
                .configId(config.getId())
                .status("created") // 초기 상태
                .totalTrades(0)
                .winningTrades(0)
                .totalProfit(BigDecimal.ZERO)
                .totalReturn(BigDecimal.ZERO)
                .maxDrawdown(BigDecimal.ZERO)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        autoTradingStatusRepository.save(status);
    }

    /**
     * 설정 ID 생성
     */
    private String generateConfigId() {
        return "CONFIG-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12).toUpperCase();
    }

    /**
     * 상태 ID 생성
     */
    private String generateStatusId() {
        return "STATUS-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12).toUpperCase();
    }

    /**
     * AutoTradingConfig를 Response DTO로 변환
     */
    private AutoTradingConfigDto.Response convertToConfigResponse(AutoTradingConfig config) {
        return AutoTradingConfigDto.Response.builder()
                .id(config.getId())
                .strategyName(config.getStrategyName())
                .symbol(config.getSymbol())
                .capital(config.getCapital())
                .maxPositionSize(config.getMaxPositionSize())
                .stopLossPercent(config.getStopLossPercent())
                .takeProfitPercent(config.getTakeProfitPercent())
                .isActive(config.getIsActive())
                .createdAt(config.getCreatedAt())
                .updatedAt(config.getUpdatedAt())
                .build();
    }

    /**
     * AutoTradingStatus를 Response DTO로 변환
     */
    private AutoTradingStatusDto.Response convertToStatusResponse(AutoTradingStatus status) {
        return AutoTradingStatusDto.Response.builder()
                .id(status.getId())
                .configId(status.getConfigId())
                .status(status.getStatus())
                .totalTrades(status.getTotalTrades())
                .winningTrades(status.getWinningTrades())
                .totalProfit(status.getTotalProfit())
                .totalReturn(status.getTotalReturn())
                .maxDrawdown(status.getMaxDrawdown())
                .startedAt(status.getStartedAt())
                .stoppedAt(status.getStoppedAt())
                .createdAt(status.getCreatedAt())
                .updatedAt(status.getUpdatedAt())
                .build();
    }
}