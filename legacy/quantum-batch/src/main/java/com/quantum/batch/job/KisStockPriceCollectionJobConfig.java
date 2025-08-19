package com.quantum.batch.job;

import com.quantum.batch.listener.JobExecutionListener;
import com.quantum.batch.listener.StepExecutionListener;
import com.quantum.batch.step.KisStockPriceItemProcessor;
import com.quantum.batch.step.KisStockPriceItemReader;
import com.quantum.batch.step.KisStockPriceItemWriter;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.launch.support.RunIdIncrementer;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.task.TaskExecutor;
import org.springframework.transaction.PlatformTransactionManager;

/**
 * KIS 주식 시세 수집 배치 Job 설정
 * 여러 종목의 실시간 시세를 수집하여 DB에 저장
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class KisStockPriceCollectionJobConfig {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager transactionManager;
    private final TaskExecutor batchTaskExecutor;
    private final JobExecutionListener jobExecutionListener;
    private final StepExecutionListener stepExecutionListener;
    private final KisStockPriceItemProcessor kisStockPriceItemProcessor;

    @Bean
    public Job kisStockPriceCollectionJob() {
        return new JobBuilder("kisStockPriceCollectionJob", jobRepository)
                .incrementer(new RunIdIncrementer())
                .listener(jobExecutionListener)
                .start(kisStockPriceCollectionStep())
                .build();
    }

    @Bean
    public Step kisStockPriceCollectionStep() {
        return new StepBuilder("kisStockPriceCollectionStep", jobRepository)
                .<String, String>chunk(10, transactionManager)
                .reader(kisStockPriceItemReader())
                .processor(kisStockPriceItemProcessor)
                .writer(kisStockPriceItemWriter())
                .listener(stepExecutionListener)
                .taskExecutor(batchTaskExecutor)
                .build();
    }

    @Bean
    public KisStockPriceItemReader kisStockPriceItemReader() {
        return new KisStockPriceItemReader();
    }


    @Bean
    public KisStockPriceItemWriter kisStockPriceItemWriter() {
        return new KisStockPriceItemWriter();
    }
}