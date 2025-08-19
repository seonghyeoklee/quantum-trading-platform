package com.quantum.batch.listener;

import java.time.LocalDateTime;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.ExitStatus;
import org.springframework.batch.core.StepExecution;
import org.springframework.stereotype.Component;

/** Spring Batch Step 실행 리스너 Step별 상세한 실행 정보 및 진행 상황 모니터링 */
@Slf4j
@Component
public class StepExecutionListener implements org.springframework.batch.core.StepExecutionListener {

    /** Step 실행 전 호출 Step 시작 정보 및 초기 설정 로깅 */
    @Override
    public void beforeStep(final StepExecution stepExecution) {
        String stepName = stepExecution.getStepName();
        LocalDateTime startTime = stepExecution.getStartTime();

        if (startTime != null) {
            log.info("Starting Step: {} at {}", stepName, startTime);
        } else {
            log.info("Starting Step: {} (startTime is null)", stepName);
        }

        // Step 실행 컨텍스트에 시작 정보 저장
        stepExecution.getExecutionContext().put("step.start.timestamp", System.currentTimeMillis());
        stepExecution.getExecutionContext().put("step.name", stepName);

        // 청크 크기 정보 로깅 (가능한 경우)
        try {
            long commitCount = stepExecution.getCommitCount();
            log.debug("Step commit count: {}", commitCount);
        } catch (Exception e) {
            log.debug("Could not determine commit count: {}", e.getMessage());
        }
    }

    /** Step 실행 후 호출 Step 결과 및 성능 통계 로깅 */
    @Override
    public ExitStatus afterStep(final StepExecution stepExecution) {
        String stepName = stepExecution.getStepName();
        ExitStatus exitStatus = stepExecution.getExitStatus();

        LocalDateTime startTime = stepExecution.getStartTime();
        LocalDateTime endTime = stepExecution.getEndTime();

        // Null 체크 후 duration 계산
        long durationSeconds = 0;
        if (startTime != null && endTime != null) {
            durationSeconds = java.time.Duration.between(startTime, endTime).getSeconds();
        } else {
            log.warn("Step {} has null time values - startTime: {}, endTime: {}", 
                    stepName, startTime, endTime);
            // 실행 컨텍스트에서 시작 시간 가져오기 시도
            try {
                Long startTimestamp = (Long) stepExecution.getExecutionContext().get("step.start.timestamp");
                if (startTimestamp != null) {
                    durationSeconds = (System.currentTimeMillis() - startTimestamp) / 1000;
                }
            } catch (Exception e) {
                log.debug("Could not calculate duration from execution context: {}", e.getMessage());
            }
        }

        // 기본 실행 정보
        log.info(
                "Step Completed: {} | Status: {} | Duration: {}s",
                stepName,
                exitStatus.getExitCode(),
                durationSeconds);

        // 처리 통계
        logProcessingStatistics(stepExecution, durationSeconds);

        // 오류 정보 (있는 경우)
        if (!exitStatus.getExitCode().equals(ExitStatus.COMPLETED.getExitCode())) {
            logStepErrors(stepExecution);
        }

        return exitStatus;
    }

    /** Step 처리 통계 정보 로깅 */
    private void logProcessingStatistics(
            final StepExecution stepExecution, final long durationSeconds) {
        long readCount = stepExecution.getReadCount();
        long writeCount = stepExecution.getWriteCount();
        long skipCount = stepExecution.getSkipCount();
        long filterCount = stepExecution.getFilterCount();
        long commitCount = stepExecution.getCommitCount();
        long rollbackCount = stepExecution.getRollbackCount();

        log.info("Processing Statistics:");
        log.info(
                "  Read: {} | Written: {} | Skipped: {} | Filtered: {}",
                readCount,
                writeCount,
                skipCount,
                filterCount);
        log.info("  Commits: {} | Rollbacks: {}", commitCount, rollbackCount);

        // 성능 지표 계산
        if (durationSeconds > 0) {
            double itemsPerSecond = (double) readCount / durationSeconds;
            double writesPerSecond = (double) writeCount / durationSeconds;

            log.info("Performance Metrics:");
            log.info(
                    "  Read Rate: {:.2f} items/sec | Write Rate: {:.2f} items/sec",
                    itemsPerSecond,
                    writesPerSecond);
        }

        // 처리 효율성 계산
        if (readCount > 0) {
            double writeEfficiency = ((double) writeCount / readCount) * 100;
            double skipRate = ((double) skipCount / readCount) * 100;

            log.info("Efficiency Metrics:");
            log.info("  Write Efficiency: {:.2f}% | Skip Rate: {:.2f}%", writeEfficiency, skipRate);
        }

        // 메모리 사용량 정보 (선택적)
        logMemoryUsage();
    }

    /** Step 오류 정보 로깅 */
    private void logStepErrors(final StepExecution stepExecution) {
        log.warn("Step completed with errors: {}", stepExecution.getStepName());

        if (!stepExecution.getFailureExceptions().isEmpty()) {
            log.error("Step Failure Exceptions:");
            stepExecution
                    .getFailureExceptions()
                    .forEach(
                            exception ->
                                    log.error(
                                            "  - {}: {}",
                                            exception.getClass().getSimpleName(),
                                            exception.getMessage()));
        }

        // 스킵된 아이템이 있는 경우
        if (stepExecution.getSkipCount() > 0) {
            log.warn(
                    "Items were skipped during processing. Skip count: {}",
                    stepExecution.getSkipCount());
        }

        // 롤백이 발생한 경우
        if (stepExecution.getRollbackCount() > 0) {
            log.warn(
                    "Rollbacks occurred during processing. Rollback count: {}",
                    stepExecution.getRollbackCount());
        }
    }

    /** 현재 메모리 사용량 로깅 */
    private void logMemoryUsage() {
        Runtime runtime = Runtime.getRuntime();
        long totalMemory = runtime.totalMemory();
        long freeMemory = runtime.freeMemory();
        long usedMemory = totalMemory - freeMemory;
        long maxMemory = runtime.maxMemory();

        double usedMemoryMB = usedMemory / (1024.0 * 1024.0);
        double maxMemoryMB = maxMemory / (1024.0 * 1024.0);
        double memoryUsagePercent = (usedMemoryMB / maxMemoryMB) * 100;

        log.debug(
                "Memory Usage: {:.2f}MB / {:.2f}MB ({:.1f}%)",
                usedMemoryMB, maxMemoryMB, memoryUsagePercent);

        // 메모리 사용량이 높은 경우 경고
        if (memoryUsagePercent > 80) {
            log.warn(
                    "High memory usage detected: {:.1f}%. Consider increasing heap size or optimizing batch size.",
                    memoryUsagePercent);
        }
    }
}
