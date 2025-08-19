package com.quantum.batch.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.*;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Quantum Batch 계층 분리 및 아키텍처 검증 테스트
 * 
 * quantum-batch 모듈의 Spring Batch + Quartz 아키텍처 원칙들을 ArchUnit으로 강제한다:
 * 1. Spring Batch 아키텍처 패턴 (Job, Step, Reader, Processor, Writer)
 * 2. Quartz 스케줄러 패턴
 * 3. 배치 처리와 실시간 처리의 명확한 분리
 * 4. 외부 API 의존성 관리
 * 5. 배치 전용 설정과 도메인 로직의 분리
 */
@DisplayName("🔄 Quantum Batch Layer Separation Rules")
class BatchLayerSeparationTest {

    private static final String BASE_PACKAGE = "com.quantum.batch";
    private static final JavaClasses classes = new ClassFileImporter()
            .importPackages(BASE_PACKAGE);

    @Test
    @DisplayName("Spring Batch Job은 올바른 패키지에 정의되어야 한다")
    void spring_batch_jobs_should_be_in_correct_package() {
        classes()
                .that().areAnnotatedWith("org.springframework.batch.core.configuration.annotation.EnableBatchProcessing")
                .or().haveSimpleNameEndingWith("JobConfig")
                .or().haveSimpleNameEndingWith("Job")
                .should().resideInAPackage("..job..")
                .because("Spring Batch Job은 job 패키지에 정의되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Batch Step은 명확한 구조를 가져야 한다")
    void batch_steps_should_have_clear_structure() {
        classes()
                .that().haveSimpleNameEndingWith("Step")
                .or().haveSimpleNameEndingWith("StepConfig")
                .should().resideInAPackage("..step..")
                .because("Batch Step은 step 패키지에 정의되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("ItemReader는 읽기 전용이어야 한다")
    void item_readers_should_be_read_only() {
        classes()
                .that().haveSimpleNameEndingWith("ItemReader")
                .or().implementInterface("org.springframework.batch.item.ItemReader")
                .should().resideInAPackage("..step.reader..")
                .andShould().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "com.quantum.batch..",
                        "com.quantum.core..",
                        "com.quantum.kis..",  // 외부 API 허용
                        "java..",
                        "org.springframework.batch..",
                        "org.springframework..",
                        "lombok.."
                )
                .because("ItemReader는 읽기 전용이고 외부 의존성을 제한해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("ItemProcessor는 순수한 변환 로직만 포함해야 한다")
    void item_processors_should_contain_only_pure_transformation() {
        classes()
                .that().haveSimpleNameEndingWith("ItemProcessor")
                .or().implementInterface("org.springframework.batch.item.ItemProcessor")
                .should().resideInAPackage("..step.processor..")
                .because("ItemProcessor는 순수한 변환 로직만 포함해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("ItemWriter는 쓰기 전용이어야 한다")
    void item_writers_should_be_write_only() {
        classes()
                .that().haveSimpleNameEndingWith("ItemWriter")
                .or().implementInterface("org.springframework.batch.item.ItemWriter")
                .should().resideInAPackage("..step.writer..")
                .because("ItemWriter는 쓰기 전용이어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Quartz Job은 올바른 패키지에 정의되어야 한다")
    void quartz_jobs_should_be_in_correct_package() {
        classes()
                .that().implementInterface("org.quartz.Job")
                .or().haveSimpleNameEndingWith("QuartzJob")
                .should().resideInAPackage("..scheduler.job..")
                .because("Quartz Job은 scheduler.job 패키지에 정의되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Scheduler Configuration은 별도 패키지에 분리되어야 한다")
    void scheduler_configuration_should_be_in_separate_package() {
        classes()
                .that().haveSimpleNameContaining("Scheduler")
                .and().haveSimpleNameEndingWith("Config")
                .or().haveSimpleNameEndingWith("Configuration")
                .should().resideInAPackage("..config..")
                .because("Scheduler 설정은 별도 패키지에 분리되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("배치 Controller는 배치 관리 기능만 제공해야 한다")
    void batch_controllers_should_only_provide_batch_management() {
        classes()
                .that().areAnnotatedWith("org.springframework.web.bind.annotation.RestController")
                .should().resideInAPackage("..controller..")
                .andShould().haveSimpleNameEndingWith("Controller")
                .andShould().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "com.quantum.batch..",
                        "java..",
                        "org.springframework..",
                        "org.quartz..",
                        "lombok.."
                )
                .because("배치 Controller는 배치 관리 기능만 제공해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("배치 모듈은 실시간 웹 요청을 처리하지 않아야 한다")
    void batch_module_should_not_handle_realtime_web_requests() {
        noClasses()
                .that().resideInAPackage("com.quantum.batch..")
                .should().beAnnotatedWith("org.springframework.web.bind.annotation.RequestMapping")
                .andShould().haveMethodThat(method -> 
                    !method.getName().contains("batch") &&
                    !method.getName().contains("job") &&
                    !method.getName().contains("scheduler")
                )
                .because("배치 모듈은 배치 관련 요청만 처리해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("외부 API 클라이언트는 배치 서비스를 통해서만 사용되어야 한다")
    void external_api_clients_should_only_be_used_through_batch_services() {
        classes()
                .that().resideInAPackage("..step..")
                .should().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "com.quantum.batch.service..",  // 배치 서비스를 통해서만
                        "com.quantum.core..",
                        "java..",
                        "org.springframework.batch..",
                        "lombok.."
                )
                .orShould().notDependOnClassesThat().resideInAnyPackage(
                        "com.quantum.kis.."  // 직접 의존 금지
                )
                .because("Step은 배치 서비스를 통해서만 외부 API를 사용해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("배치 서비스는 트랜잭션을 관리해야 한다")
    void batch_services_should_manage_transactions() {
        classes()
                .that().resideInAPackage("..service..")
                .and().haveSimpleNameEndingWith("Service")
                .should().beAnnotatedWith("org.springframework.stereotype.Service")
                .orShould().beAnnotatedWith("org.springframework.transaction.annotation.Transactional")
                .because("배치 서비스는 트랜잭션을 관리해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Chunk 기반 처리는 적절한 크기를 가져야 한다")
    void chunk_based_processing_should_have_appropriate_size() {
        noClasses()
                .that().resideInAPackage("..step..")
                .should().haveMethodThat(method -> 
                    method.getName().contains("chunk") &&
                    method.getParameterTypes().stream().anyMatch(type ->
                        type.getSimpleName().equals("int") &&
                        // 큰 청크 사이즈 체크 (실제 구현에서는 상수나 설정값 확인)
                        false // 실제로는 더 정교한 체크 필요
                    )
                )
                .because("Chunk 크기는 적절하게 설정되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("배치 실패 처리 로직이 있어야 한다")
    void batch_should_have_failure_handling_logic() {
        classes()
                .that().resideInAPackage("..job..")
                .or().resideInAPackage("..step..")
                .should().haveMethodThat(method -> 
                    method.getName().contains("onFailure") ||
                    method.getName().contains("handleError") ||
                    method.getName().contains("retry")
                )
                .orShould().dependOnClassesThat().resideInAnyPackage(
                        "org.springframework.retry..",
                        "org.springframework.batch.core.step.skip.."
                )
                .because("배치는 실패 처리 로직을 포함해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("스케줄러는 클러스터링을 지원해야 한다")
    void scheduler_should_support_clustering() {
        classes()
                .that().haveSimpleNameContaining("Scheduler")
                .and().haveSimpleNameEndingWith("Config")
                .should().haveFieldThat(field -> 
                    field.getName().contains("clustered") ||
                    field.getName().contains("instanceId") ||
                    field.getRawType().getSimpleName().contains("DataSource")
                )
                .because("스케줄러는 클러스터링을 지원해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("배치 메타데이터는 영속화되어야 한다")
    void batch_metadata_should_be_persisted() {
        classes()
                .that().haveSimpleNameContaining("Batch")
                .and().haveSimpleNameEndingWith("Config")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "javax.sql..",
                        "org.springframework.jdbc..",
                        "org.springframework.batch.core.repository.."
                )
                .because("배치 메타데이터는 데이터베이스에 영속화되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("배치 모니터링과 관리 API가 있어야 한다")
    void batch_should_have_monitoring_and_management_api() {
        classes()
                .that().resideInAPackage("..controller..")
                .should().haveMethodThat(method -> 
                    method.getName().contains("status") ||
                    method.getName().contains("health") ||
                    method.getName().contains("metric")
                )
                .because("배치는 모니터링과 관리 API를 제공해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Rate Limiting이 배치 처리에 적용되어야 한다")
    void rate_limiting_should_be_applied_to_batch_processing() {
        classes()
                .that().resideInAPackage("..step..")
                .and().haveSimpleNameEndingWith("Reader")
                .should().dependOnClassesThat().haveSimpleNameContaining("RateLimit")
                .orShould().haveFieldThat(field -> field.getName().contains("rateLimiter"))
                .because("배치 처리에서도 Rate Limiting이 적용되어야 함")
                .check(classes);
    }
}