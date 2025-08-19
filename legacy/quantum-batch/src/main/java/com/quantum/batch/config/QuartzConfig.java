package com.quantum.batch.config;

import java.util.TimeZone;
import lombok.extern.slf4j.Slf4j;
import org.quartz.CronScheduleBuilder;
import org.quartz.JobBuilder;
import org.quartz.JobDetail;
import org.quartz.JobExecutionContext;
import org.quartz.Trigger;
import org.quartz.TriggerBuilder;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.JobParameters;
import org.springframework.batch.core.JobParametersBuilder;
import org.springframework.batch.core.configuration.JobLocator;
import org.springframework.batch.core.launch.JobLauncher;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.lang.NonNull;
import org.springframework.scheduling.quartz.SpringBeanJobFactory;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

/**
 * Quartz 스케줄러 설정 주식 시세 수집 Job들의 스케줄링 설정
 */
@Slf4j
@Configuration
public class QuartzConfig {

    /**
     * KIS 주식 시세 수집 JobDetail 설정 Spring Batch Job을 Quartz에서 실행하기 위한 JobDetail
     */
    @Bean
    public JobDetail kisStockPriceCollectionJobDetail() {
        return JobBuilder.newJob(com.quantum.batch.job.KisStockPriceCollectionQuartzJob.class)
                .withIdentity("kisStockPriceCollectionJob", "quantum-trading")
                .withDescription("KIS API를 통한 주식 시세 수집 작업")
                .storeDurably()
                .build();
    }

    /**
     * 테스트용 실시간 시세 수집 트리거 (매분 실행)
     * 실제 운영시에는 "0 * 9-15 ? * MON-FRI"로 변경
     */
    @Bean
    public Trigger marketHoursTrigger() {
        return TriggerBuilder.newTrigger()
                .forJob(kisStockPriceCollectionJobDetail())
                .withIdentity("marketHoursTrigger", "quantum-trading")
                .withDescription("테스트용 실시간 시세 수집 (매분 실행)")
                .withSchedule(CronScheduleBuilder.cronSchedule("0 * * * * ?")
                        .inTimeZone(TimeZone.getTimeZone("Asia/Seoul")))
                .build();
    }

    /**
     * 장후 종합 시세 수집 트리거 (평일 16:00, 1회) 장 마감 후 최종 시세 수집
     */
    @Bean
    public Trigger afterMarketTrigger() {
        return TriggerBuilder.newTrigger()
                .forJob(kisStockPriceCollectionJobDetail())
                .withIdentity("afterMarketTrigger", "quantum-trading")
                .withDescription("장후 최종 시세 수집 (평일 16:00)")
                .withSchedule(CronScheduleBuilder.cronSchedule("0 0 16 ? * MON-FRI")
                        .inTimeZone(TimeZone.getTimeZone("Asia/Seoul")))
                .build();
    }

    /**
     * KIS 멀티 주식 시세 수집 JobDetail 설정 (성능 최적화 버전)
     * 30종목씩 배치 처리로 API 호출 횟수 90% 감소
     */
    @Bean
    public JobDetail kisMultiStockPriceCollectionJobDetail() {
        return JobBuilder.newJob(com.quantum.batch.job.KisMultiStockPriceCollectionQuartzJob.class)
                .withIdentity("kisMultiStockPriceCollectionJob", "quantum-trading")
                .withDescription("KIS API 멀티 조회를 통한 고성능 주식 시세 수집 작업")
                .storeDurably()
                .build();
    }

    /**
     * 멀티 조회 테스트용 트리거 (매 2분 실행)
     * 성능 비교를 위해 기존 단일 조회와 함께 실행
     */
    @Bean
    public Trigger multiMarketHoursTrigger() {
        return TriggerBuilder.newTrigger()
                .forJob(kisMultiStockPriceCollectionJobDetail())
                .withIdentity("multiMarketHoursTrigger", "quantum-trading")
                .withDescription("멀티 조회 테스트용 고성능 시세 수집 (매 2분 실행)")
                .withSchedule(CronScheduleBuilder.cronSchedule("0 */2 * * * ?")
                        .inTimeZone(TimeZone.getTimeZone("Asia/Seoul")))
                .build();
    }


    /**
     * Spring Bean으로 직접 의존성을 주입받는 Job 실행기
     */
    @Service
    public static class BatchJobExecutor {

        private final JobLauncher jobLauncher;
        private final JobLocator jobLocator;

        public BatchJobExecutor(JobLauncher jobLauncher, JobLocator jobLocator) {
            this.jobLauncher = jobLauncher;
            this.jobLocator = jobLocator;
        }

        public void executeKisStockPriceJob(String triggerName) throws Exception {
            Job job = jobLocator.getJob("kisStockPriceCollectionJob");
            JobParameters jobParameters = new JobParametersBuilder()
                    .addLong("time", System.currentTimeMillis())
                    .addString("trigger", triggerName)
                    .toJobParameters();

            var execution = jobLauncher.run(job, jobParameters);

            log.info("KIS 주식 시세 수집 배치 작업 완료: {} - {}",
                    execution.getStatus(), execution.getEndTime());
        }
    }

    /**
     * Spring Boot Quartz 자동 설정이 Spring Bean으로 Job을 관리하도록 설정
     */
    @Bean
    public SpringBeanJobFactory springBeanJobFactory() {
        return new SpringBeanJobFactory();
    }
}
