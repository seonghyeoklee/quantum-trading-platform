package com.quantum.batch.job;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.quartz.Job;
import org.quartz.JobExecutionContext;
import org.quartz.JobExecutionException;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

/**
 * KIS 멀티 주식 시세 수집 Quartz Job
 * 
 * 성능 최적화된 멀티 조회 방식으로 주식 시세 수집
 * - 30종목씩 배치 처리로 API 호출 횟수 90% 감소
 * - Rate Limiting 효율성 대폭 향상
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisMultiStockPriceCollectionQuartzJob implements Job {

    private final JobLauncher jobLauncher;
    private final KisMultiStockPriceCollectionJobConfig jobConfig;

    @Override
    public void execute(JobExecutionContext context) throws JobExecutionException {
        
        String jobName = "kisMultiStockPriceCollectionJob";
        LocalDateTime startTime = LocalDateTime.now();
        
        log.info("🚀 KIS Multi Stock Price Collection Job started at: {}", startTime);
        
        try {
            // Job 파라미터 생성 (실행 시간을 포함하여 중복 실행 방지)
            org.springframework.batch.core.JobParameters jobParameters = new JobParametersBuilder()
                    .addString("startTime", startTime.toString())
                    .addLong("timestamp", System.currentTimeMillis())
                    .toJobParameters();

            // 멀티 주식 시세 수집 Job 실행
            org.springframework.batch.core.JobExecution jobExecution = jobLauncher.run(
                    jobConfig.kisMultiStockPriceCollectionJob(), 
                    jobParameters
            );

            // 실행 결과 로깅
            LocalDateTime endTime = LocalDateTime.now();
            long durationSeconds = java.time.Duration.between(startTime, endTime).getSeconds();
            
            log.info("✅ KIS Multi Stock Price Collection Job completed:");
            log.info("   📊 Status: {}", jobExecution.getStatus());
            log.info("   ⏱️  Duration: {}s", durationSeconds);
            log.info("   📈 Performance: Multi-batch processing (30 stocks per API call)");
            
            if (jobExecution.getStatus().isUnsuccessful()) {
                log.error("❌ Job failed with exit status: {}", jobExecution.getExitStatus());
                throw new JobExecutionException("KIS Multi Stock Price Collection Job failed");
            }

        } catch (Exception e) {
            LocalDateTime endTime = LocalDateTime.now();
            long durationSeconds = java.time.Duration.between(startTime, endTime).getSeconds();
            
            log.error("💥 KIS Multi Stock Price Collection Job failed after {}s", durationSeconds, e);
            throw new JobExecutionException("Failed to execute KIS Multi Stock Price Collection Job", e);
        }
    }
}