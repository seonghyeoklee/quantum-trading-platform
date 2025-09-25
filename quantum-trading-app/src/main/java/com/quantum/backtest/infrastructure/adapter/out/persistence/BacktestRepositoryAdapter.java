package com.quantum.backtest.infrastructure.adapter.out.persistence;

import com.quantum.backtest.application.port.out.BacktestRepositoryPort;
import com.quantum.backtest.domain.Backtest;
import com.quantum.backtest.domain.BacktestId;
import com.quantum.backtest.domain.BacktestResult;
import com.quantum.backtest.infrastructure.persistence.BacktestEntity;
import com.quantum.backtest.infrastructure.persistence.JpaBacktestRepository;
import com.quantum.backtest.infrastructure.persistence.TradeEntity;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Repository;

import java.util.Optional;

/**
 * 백테스팅 Repository 어댑터
 * Application Port를 구현하여 JPA Repository와 도메인을 연결
 */
@Repository
public class BacktestRepositoryAdapter implements BacktestRepositoryPort {

    private final JpaBacktestRepository jpaRepository;

    public BacktestRepositoryAdapter(JpaBacktestRepository jpaRepository) {
        this.jpaRepository = jpaRepository;
    }

    @Override
    public Backtest save(Backtest backtest) {
        String backtestUuid = backtest.getId().value();

        if (backtestUuid != null && !backtestUuid.isEmpty()) {
            // 기존 엔티티가 있는지 확인 (UUID로 조회)
            Optional<BacktestEntity> existingEntityOpt = jpaRepository.findByBacktestUuid(backtestUuid);

            if (existingEntityOpt.isPresent()) {
                // 기존 엔티티 업데이트
                BacktestEntity existingEntity = existingEntityOpt.get();
                updateExistingEntity(existingEntity, backtest);
                BacktestEntity savedEntity = jpaRepository.save(existingEntity);
                return savedEntity.toDomain();
            }
        }

        // 새 엔티티 생성 (Long PK는 Hibernate가 자동 생성)
        BacktestEntity entity = BacktestEntity.from(backtest);
        BacktestEntity savedEntity = jpaRepository.save(entity);
        return savedEntity.toDomain();
    }

    private void updateExistingEntity(BacktestEntity existingEntity, Backtest backtest) {
        // 기본 정보 업데이트
        existingEntity.setStatus(backtest.getStatus());
        existingEntity.setStartedAt(backtest.getStartedAt());
        existingEntity.setCompletedAt(backtest.getCompletedAt());
        existingEntity.setErrorMessage(backtest.getErrorMessage());
        existingEntity.setProgressPercentage(backtest.getProgressPercentage());

        // 결과 정보 업데이트
        if (backtest.getResult() != null) {
            BacktestResult result = backtest.getResult();
            existingEntity.setTotalReturn(result.totalReturn());
            existingEntity.setAnnualizedReturn(result.annualizedReturn());
            existingEntity.setMaxDrawdown(result.maxDrawdown());
            existingEntity.setTotalTrades(result.totalTrades());
            existingEntity.setWinTrades(result.winTrades());
            existingEntity.setLossTrades(result.lossTrades());
            existingEntity.setWinRate(result.winRate());
            existingEntity.setSharpeRatio(result.sharpeRatio());
            existingEntity.setFinalCapital(result.finalCapital());
            existingEntity.setTotalFees(result.totalFees());
        }

        // 거래 내역은 기존 것을 유지하고 새것만 추가 (현재는 단순화)
        existingEntity.getTrades().clear();
        backtest.getTrades().forEach(trade -> {
            existingEntity.getTrades().add(TradeEntity.from(trade, existingEntity));
        });
    }


    @Override
    public Optional<Backtest> findById(BacktestId id) {
        return jpaRepository.findByBacktestUuid(id.value())
                .map(BacktestEntity::toDomain);
    }

    @Override
    public Page<Backtest> findAll(Pageable pageable) {
        return jpaRepository.findAllByOrderByCreatedAtDesc(pageable)
                .map(BacktestEntity::toDomain);
    }

    @Override
    public void deleteById(BacktestId id) {
        jpaRepository.findByBacktestUuid(id.value())
                .ifPresent(entity -> jpaRepository.deleteById(entity.getId()));
    }

    @Override
    public boolean existsById(BacktestId id) {
        return jpaRepository.findByBacktestUuid(id.value()).isPresent();
    }
}