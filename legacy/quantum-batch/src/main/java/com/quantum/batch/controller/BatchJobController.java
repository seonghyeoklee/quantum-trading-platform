package com.quantum.batch.controller;

import com.quantum.core.domain.model.common.BatchJobStatus;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.*;
import org.springframework.batch.core.explore.JobExplorer;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.batch.core.repository.JobExecutionAlreadyRunningException;
import org.springframework.batch.core.repository.JobInstanceAlreadyCompleteException;
import org.springframework.batch.core.repository.JobRestartException;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 배치 Job 실행 및 상태 조회 Controller
 */
@Slf4j
@RestController
@RequestMapping("/api/batch/jobs")
@RequiredArgsConstructor
@Tag(name = "Batch Job API", description = "Spring Batch Job 실행 및 상태 관리")
public class BatchJobController {

    private final JobLauncher jobLauncher;
    private final JobExplorer jobExplorer;
    private final Job kisStockPriceCollectionJob;

    @PostMapping("/kis-stock-price/run")
    @Operation(summary = "KIS 주식 시세 수집 Job 실행", description = "KIS API를 통해 주요 종목의 시세를 수집하는 배치 Job을 실행합니다")
    public ResponseEntity<?> runKisStockPriceJob() {
        try {
            JobParameters jobParameters = new JobParametersBuilder()
                    .addLong("timestamp", System.currentTimeMillis())
                    .toJobParameters();

            JobExecution jobExecution = jobLauncher.run(kisStockPriceCollectionJob, jobParameters);
            
            log.info("Batch: KIS stock price collection job started - ID: {}", jobExecution.getId());

            return ResponseEntity.ok(Map.of(
                    "jobExecutionId", jobExecution.getId(),
                    "jobName", "kisStockPriceCollectionJob",
                    "status", jobExecution.getStatus().toString(),
                    "startTime", jobExecution.getStartTime(),
                    "message", "KIS 주식 시세 수집 Job이 시작되었습니다"
            ));

        } catch (JobExecutionAlreadyRunningException e) {
            log.warn("Batch: KIS stock price collection job is already running");
            return ResponseEntity.badRequest().body(Map.of(
                    "error", BatchJobStatus.ALREADY_RUNNING.getCode(),
                    "message", BatchJobStatus.ALREADY_RUNNING.getDescription()
            ));

        } catch (JobInstanceAlreadyCompleteException e) {
            log.warn("Batch: KIS stock price collection job instance already completed");
            return ResponseEntity.badRequest().body(Map.of(
                    "error", BatchJobStatus.ALREADY_COMPLETED.getCode(), 
                    "message", BatchJobStatus.ALREADY_COMPLETED.getDescription()
            ));

        } catch (JobRestartException | JobParametersInvalidException e) {
            log.error("Batch: Failed to start KIS stock price collection job", e);
            return ResponseEntity.internalServerError().body(Map.of(
                    "error", BatchJobStatus.START_FAILED.getCode(),
                    "message", BatchJobStatus.START_FAILED.getDescription() + ": " + e.getMessage()
            ));
        }
    }

    @GetMapping("/kis-stock-price/status")
    @Operation(summary = "KIS 주식 시세 수집 Job 상태 조회", description = "KIS 주식 시세 수집 Job의 최근 실행 상태를 조회합니다")
    public ResponseEntity<?> getKisStockPriceJobStatus() {
        try {
            List<JobInstance> jobInstances = jobExplorer.getJobInstances("kisStockPriceCollectionJob", 0, 1);
            
            if (jobInstances.isEmpty()) {
                return ResponseEntity.ok(Map.of(
                        "jobName", "kisStockPriceCollectionJob",
                        "status", BatchJobStatus.NEVER_EXECUTED.getCode(),
                        "message", BatchJobStatus.NEVER_EXECUTED.getDescription()
                ));
            }

            JobInstance latestInstance = jobInstances.get(0);
            List<JobExecution> executions = jobExplorer.getJobExecutions(latestInstance);
            
            if (executions.isEmpty()) {
                return ResponseEntity.ok(Map.of(
                        "jobName", "kisStockPriceCollectionJob",
                        "status", BatchJobStatus.NO_EXECUTIONS.getCode(),
                        "message", BatchJobStatus.NO_EXECUTIONS.getDescription()
                ));
            }

            JobExecution latestExecution = executions.get(0);
            
            return ResponseEntity.ok(Map.of(
                    "jobExecutionId", latestExecution.getId(),
                    "jobName", "kisStockPriceCollectionJob",
                    "status", latestExecution.getStatus().toString(),
                    "startTime", latestExecution.getStartTime(),
                    "endTime", latestExecution.getEndTime(),
                    "duration", latestExecution.getEndTime() != null ? 
                        java.time.Duration.between(
                            latestExecution.getStartTime(),
                            latestExecution.getEndTime()
                        ).toMillis() + "ms" : null,
                    "exitCode", latestExecution.getExitStatus().getExitCode(),
                    "exitDescription", latestExecution.getExitStatus().getExitDescription()
            ));

        } catch (Exception e) {
            log.error("Batch: Failed to get KIS stock price job status", e);
            return ResponseEntity.internalServerError().body(Map.of(
                    "error", BatchJobStatus.FAILED.getCode(),
                    "message", "Job 상태 조회에 실패했습니다: " + e.getMessage()
            ));
        }
    }

    @GetMapping("/status")
    @Operation(summary = "모든 배치 Job 상태 조회", description = "시스템의 모든 배치 Job 상태를 조회합니다")
    public ResponseEntity<?> getAllJobsStatus() {
        try {
            List<String> jobNames = jobExplorer.getJobNames();
            
            return ResponseEntity.ok(Map.of(
                    "totalJobs", jobNames.size(),
                    "jobNames", jobNames,
                    "message", "배치 Job 목록 조회 완료"
            ));

        } catch (Exception e) {
            log.error("Batch: Failed to get all jobs status", e);
            return ResponseEntity.internalServerError().body(Map.of(
                    "error", BatchJobStatus.FAILED.getCode(),
                    "message", "전체 Job 상태 조회에 실패했습니다: " + e.getMessage()
            ));
        }
    }
}