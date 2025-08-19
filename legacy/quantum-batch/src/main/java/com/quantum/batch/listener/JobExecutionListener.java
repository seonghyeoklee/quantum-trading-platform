package com.quantum.batch.listener;

import java.time.Duration;
import java.time.LocalDateTime;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.BatchStatus;
import org.springframework.batch.core.JobExecution;
import org.springframework.batch.core.StepExecution;
import org.springframework.stereotype.Component;

/** Spring Batch Job 실행 리스너 Job 시작/종료 시점에 상세한 로깅 및 모니터링 정보 제공 */
@Slf4j
@Component
public class JobExecutionListener implements org.springframework.batch.core.JobExecutionListener {

    /** Job 실행 전 호출 시작 시간, 파라미터 등 기본 정보 로깅 */
    @Override
    public void beforeJob(final JobExecution jobExecution) {
        String jobName = jobExecution.getJobInstance().getJobName();
        LocalDateTime startTime = jobExecution.getStartTime();

        log.info("========================================");
        log.info("Starting Job: {}", jobName);
        log.info("Job ID: {}", jobExecution.getJobId());
        log.info("Start Time: {}", startTime);
        log.info("Job Parameters: {}", jobExecution.getJobParameters().getParameters());
        log.info("========================================");

        // Job 실행 컨텍스트에 시작 정보 저장
        jobExecution.getExecutionContext().put("job.start.timestamp", System.currentTimeMillis());
        jobExecution.getExecutionContext().put("job.name", jobName);
    }

    /** Job 실행 후 호출 실행 결과, 소요 시간, 통계 정보 등 상세 로깅 */
    @Override
    public void afterJob(final JobExecution jobExecution) {
        String jobName = jobExecution.getJobInstance().getJobName();
        BatchStatus status = jobExecution.getStatus();

        LocalDateTime startTime = jobExecution.getStartTime();
        LocalDateTime endTime = jobExecution.getEndTime();

        Duration duration = Duration.between(startTime, endTime);

        log.info("========================================");
        log.info("Job Completed: {}", jobName);
        log.info("Job ID: {}", jobExecution.getJobId());
        log.info("Status: {}", status);
        log.info("Start Time: {}", startTime);
        log.info("End Time: {}", endTime);
        log.info("Duration: {} seconds", duration.getSeconds());

        // Step별 통계 정보 출력
        logStepStatistics(jobExecution);

        // 실행 결과에 따른 세부 로깅
        if (status == BatchStatus.COMPLETED) {
            logSuccessStatistics(jobExecution);
        } else if (status == BatchStatus.FAILED) {
            logFailureDetails(jobExecution);
        }

        log.info("========================================");
    }

    /** Step별 상세 통계 정보 로깅 */
    private void logStepStatistics(final JobExecution jobExecution) {
        log.info("Step Statistics:");

        for (StepExecution stepExecution : jobExecution.getStepExecutions()) {
            String stepName = stepExecution.getStepName();
            BatchStatus stepStatus = stepExecution.getStatus();

            long readCount = stepExecution.getReadCount();
            long writeCount = stepExecution.getWriteCount();
            long skipCount = stepExecution.getSkipCount();
            long filterCount = stepExecution.getFilterCount();

            Duration stepDuration =
                    Duration.between(stepExecution.getStartTime(), stepExecution.getEndTime());

            log.info(
                    "  Step: {} | Status: {} | Duration: {}s",
                    stepName,
                    stepStatus,
                    stepDuration.getSeconds());
            log.info(
                    "    Read: {} | Written: {} | Skipped: {} | Filtered: {}",
                    readCount,
                    writeCount,
                    skipCount,
                    filterCount);

            // 처리 속도 계산
            if (stepDuration.getSeconds() > 0) {
                double itemsPerSecond = (double) readCount / stepDuration.getSeconds();
                log.info("    Processing Rate: {:.2f} items/second", itemsPerSecond);
            }
        }
    }

    /** 성공한 Job의 상세 통계 로깅 */
    private void logSuccessStatistics(final JobExecution jobExecution) {
        long totalReadCount =
                jobExecution.getStepExecutions().stream()
                        .mapToLong(StepExecution::getReadCount)
                        .sum();
        long totalWriteCount =
                jobExecution.getStepExecutions().stream()
                        .mapToLong(StepExecution::getWriteCount)
                        .sum();
        long totalSkipCount =
                jobExecution.getStepExecutions().stream()
                        .mapToLong(StepExecution::getSkipCount)
                        .sum();

        log.info(
                "SUCCESS - Total Processed: {} | Written: {} | Skipped: {}",
                totalReadCount,
                totalWriteCount,
                totalSkipCount);

        // 성공률 계산
        if (totalReadCount > 0) {
            double successRate = ((double) totalWriteCount / totalReadCount) * 100;
            log.info("Success Rate: {:.2f}%", successRate);
        }
    }

    /** 실패한 Job의 상세 오류 정보 로깅 */
    private void logFailureDetails(final JobExecution jobExecution) {
        log.error("FAILED - Job execution failed");

        // Job 레벨 예외 정보
        if (!jobExecution.getAllFailureExceptions().isEmpty()) {
            log.error("Job Failure Exceptions:");
            jobExecution
                    .getAllFailureExceptions()
                    .forEach(
                            exception ->
                                    log.error(
                                            "  - {}: {}",
                                            exception.getClass().getSimpleName(),
                                            exception.getMessage()));
        }

        // Step 레벨 예외 정보
        for (StepExecution stepExecution : jobExecution.getStepExecutions()) {
            if (stepExecution.getStatus() == BatchStatus.FAILED) {
                log.error("Failed Step: {}", stepExecution.getStepName());

                if (!stepExecution.getFailureExceptions().isEmpty()) {
                    stepExecution
                            .getFailureExceptions()
                            .forEach(
                                    exception ->
                                            log.error(
                                                    "  Step Exception: {}: {}",
                                                    exception.getClass().getSimpleName(),
                                                    exception.getMessage()));
                }
            }
        }

        // 부분 처리 결과 로깅 (일부 성공한 경우)
        long totalWriteCount =
                jobExecution.getStepExecutions().stream()
                        .mapToLong(StepExecution::getWriteCount)
                        .sum();

        if (totalWriteCount > 0) {
            log.info(
                    "Partial Success - {} items were successfully processed before failure",
                    totalWriteCount);
        }
    }
}
