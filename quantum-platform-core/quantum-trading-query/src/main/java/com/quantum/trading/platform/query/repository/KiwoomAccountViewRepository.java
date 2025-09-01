package com.quantum.trading.platform.query.repository;

import com.quantum.trading.platform.query.view.KiwoomAccountView;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

/**
 * 키움증권 계좌 조회용 Repository
 * 
 * Spring Data JPA 기반으로 키움증권 계좌 정보 조회 최적화
 */
@Repository
public interface KiwoomAccountViewRepository extends JpaRepository<KiwoomAccountView, String> {

    /**
     * 키움증권 계좌번호로 조회
     */
    Optional<KiwoomAccountView> findByKiwoomAccountId(String kiwoomAccountId);

    /**
     * 사용자 ID로 키움증권 계좌 조회
     */
    Optional<KiwoomAccountView> findByUserId(String userId);

    /**
     * 활성 계좌만 조회
     */
    @Query("SELECT k FROM KiwoomAccountView k WHERE k.isActive = true")
    List<KiwoomAccountView> findAllActiveAccounts();

    /**
     * 사용자의 활성 키움증권 계좌 조회
     */
    @Query("SELECT k FROM KiwoomAccountView k WHERE k.userId = :userId AND k.isActive = true")
    Optional<KiwoomAccountView> findActiveAccountByUserId(@Param("userId") String userId);

    /**
     * 특정 기간 이후 할당된 계좌 조회
     */
    @Query("SELECT k FROM KiwoomAccountView k WHERE k.assignedAt >= :fromDate ORDER BY k.assignedAt DESC")
    List<KiwoomAccountView> findAccountsAssignedAfter(@Param("fromDate") Instant fromDate);

    /**
     * 인증 정보가 최근 업데이트된 계좌 조회
     */
    @Query("SELECT k FROM KiwoomAccountView k WHERE k.credentialsUpdatedAt >= :fromDate ORDER BY k.credentialsUpdatedAt DESC")
    List<KiwoomAccountView> findAccountsWithRecentCredentialUpdates(@Param("fromDate") Instant fromDate);

    /**
     * 유효한 인증 정보를 가진 계좌 수 조회
     */
    @Query("SELECT COUNT(k) FROM KiwoomAccountView k WHERE k.isActive = true AND k.clientId IS NOT NULL AND k.clientSecret IS NOT NULL")
    long countAccountsWithValidCredentials();

    /**
     * 키움증권 계좌번호 존재 여부 확인
     */
    boolean existsByKiwoomAccountId(String kiwoomAccountId);

    /**
     * 사용자의 키움증권 계좌 존재 여부 확인
     */
    @Query("SELECT CASE WHEN COUNT(k) > 0 THEN true ELSE false END FROM KiwoomAccountView k WHERE k.userId = :userId AND k.isActive = true")
    boolean existsActiveAccountByUserId(@Param("userId") String userId);

    /**
     * 비활성 계좌 조회
     */
    @Query("SELECT k FROM KiwoomAccountView k WHERE k.isActive = false ORDER BY k.updatedAt DESC")
    List<KiwoomAccountView> findInactiveAccounts();

    /**
     * 사용자별 키움증권 계좌 할당 여부 배치 조회
     */
    @Query("SELECT k.userId FROM KiwoomAccountView k WHERE k.userId IN :userIds AND k.isActive = true")
    List<String> findUserIdsWithActiveAccounts(@Param("userIds") List<String> userIds);
}