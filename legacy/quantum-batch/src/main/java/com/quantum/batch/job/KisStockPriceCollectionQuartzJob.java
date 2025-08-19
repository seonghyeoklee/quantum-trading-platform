package com.quantum.batch.job;

import com.quantum.batch.config.QuartzConfig;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.quartz.JobExecutionContext;
import org.springframework.lang.NonNull;
import org.springframework.scheduling.quartz.QuartzJobBean;
import org.springframework.stereotype.Component;

/**
 * KIS 주식 시세 수집을 위한 Quartz Job
 * Spring의 의존성 주입을 받는 QuartzJobBean
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class KisStockPriceCollectionQuartzJob extends QuartzJobBean {

    private final QuartzConfig.BatchJobExecutor batchJobExecutor;

    @Override
    protected void executeInternal(@NonNull JobExecutionContext context) {
        try {
            log.info("KIS 주식 시세 수집 배치 작업 시작: {}", context.getFireTime());

            batchJobExecutor.executeKisStockPriceJob(context.getTrigger().getKey().getName());

        } catch (Exception e) {
            log.error("KIS 주식 시세 수집 배치 작업 실행 중 오류 발생", e);
            throw new RuntimeException("배치 작업 실행 실패", e);
        }
    }
}