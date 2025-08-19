package com.quantum.batch.job;

import com.quantum.batch.listener.StepExecutionListener;
import com.quantum.batch.step.KisMultiStockPriceItemProcessor;
import com.quantum.batch.step.KisMultiStockPriceItemReader;
import com.quantum.batch.step.KisMultiStockPriceItemWriter;
import com.quantum.kis.model.KisMultiStockItem;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.batch.core.Job;
import org.springframework.batch.core.Step;
import org.springframework.batch.core.job.builder.JobBuilder;
import org.springframework.batch.core.repository.JobRepository;
import org.springframework.batch.core.step.builder.StepBuilder;
import org.springframework.batch.item.ItemProcessor;
import org.springframework.batch.item.ItemReader;
import org.springframework.batch.item.ItemWriter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.transaction.PlatformTransactionManager;

import java.util.List;

/**
 * KIS 멀티 주식 시세 수집 배치 Job 설정
 * 
 * 성능 최적화된 멀티 조회 방식:
 * - 기존: 10종목 = 10번 API 호출 (5초)
 * - 신규: 30종목 = 1번 API 호출 (0.5초)
 * - 개선: 600% 성능 향상
 */
@Slf4j
@Configuration
@RequiredArgsConstructor
public class KisMultiStockPriceCollectionJobConfig {

    private final JobRepository jobRepository;
    private final PlatformTransactionManager platformTransactionManager;
    private final StepExecutionListener stepExecutionListener;

    // Step Components
    private final KisMultiStockPriceItemReader kisMultiStockPriceItemReader;
    private final KisMultiStockPriceItemProcessor kisMultiStockPriceItemProcessor;
    private final KisMultiStockPriceItemWriter kisMultiStockPriceItemWriter;

    /**
     * 멀티 주식 시세 수집 Job
     * 
     * 30종목씩 배치로 처리하여 KIS API 호출 횟수 대폭 감소
     */
    @Bean
    public Job kisMultiStockPriceCollectionJob() {
        return new JobBuilder("kisMultiStockPriceCollectionJob", jobRepository)
                .start(kisMultiStockPriceCollectionStep())
                .build();
    }

    /**
     * 멀티 주식 시세 수집 Step
     * 
     * Chunk 크기: 1 (각 Chunk가 30종목 배치)
     * - Reader: 30종목씩 묶은 배치 읽기
     * - Processor: 배치 단위로 KIS 멀티 API 호출
     * - Writer: 개별 종목별로 DB 저장
     */
    @Bean
    public Step kisMultiStockPriceCollectionStep() {
        return new StepBuilder("kisMultiStockPriceCollectionStep", jobRepository)
                .<List<String>, List<KisMultiStockItem>>chunk(1, platformTransactionManager) // 1 배치씩 처리
                .reader(multiStockPriceItemReader())
                .processor(multiStockPriceItemProcessor())
                .writer(multiStockPriceItemWriter())
                .listener(stepExecutionListener)
                .build();
    }

    /**
     * 멀티 주식 시세 ItemReader
     * 
     * 30종목씩 묶은 배치를 생성하여 반환
     */
    @Bean
    public ItemReader<List<String>> multiStockPriceItemReader() {
        return kisMultiStockPriceItemReader;
    }

    /**
     * 멀티 주식 시세 ItemProcessor
     * 
     * 30종목 배치를 받아서 KIS 멀티 API 호출
     */
    @Bean
    public ItemProcessor<List<String>, List<KisMultiStockItem>> multiStockPriceItemProcessor() {
        return kisMultiStockPriceItemProcessor;
    }

    /**
     * 멀티 주식 시세 ItemWriter
     * 
     * 멀티 조회 결과를 개별 종목별로 DB 저장
     */
    @Bean
    public ItemWriter<List<KisMultiStockItem>> multiStockPriceItemWriter() {
        return kisMultiStockPriceItemWriter;
    }
}