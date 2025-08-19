package com.quantum.core.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.*;
import static com.tngtech.archunit.library.Architectures.layeredArchitecture;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Quantum Core 헥사고날 아키텍처 검증 테스트
 * 
 * 헥사고날 아키텍처(Ports and Adapters)의 핵심 원칙을 검증:
 * 1. 도메인은 외부 기술에 의존하지 않음
 * 2. 포트는 인터페이스로 정의
 * 3. 어댑터는 포트를 구현
 * 4. 의존성 방향은 안쪽으로만
 */
@DisplayName("Core Module - Hexagonal Architecture Test")
class CoreHexagonalArchitectureTest {

    private static JavaClasses classes;

    @BeforeAll
    static void setUp() {
        classes = new ClassFileImporter()
                .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
                .importPackages("com.quantum.core");
    }

    @Test
    @DisplayName("헥사고날 아키텍처 레이어 규칙을 준수해야 한다")
    void hexagonal_architecture_layers_should_be_respected() {
        layeredArchitecture()
                .consideringOnlyDependenciesInLayers()
                .layer("Domain").definedBy("..domain..")
                .layer("Application").definedBy("..application..")
                .layer("Infrastructure").definedBy("..infrastructure..")
                
                .whereLayer("Domain").mayNotAccessAnyLayer()
                .whereLayer("Application").mayOnlyAccessLayers("Domain")
                .whereLayer("Infrastructure").mayOnlyAccessLayers("Domain", "Application")
                
                .check(classes);
    }

    @Test
    @DisplayName("도메인 모델은 외부 기술에 의존하지 않아야 한다")
    void domain_models_should_not_depend_on_external_technologies() {
        noClasses()
                .that().resideInAPackage("..domain.model..")
                .should().dependOnClassesThat().resideInAPackage("..infrastructure..")
                .because("도메인 모델은 순수해야 하고 인프라스트럭처에 의존하지 않아야 함")
                .check(classes);
    }

    @Test
    @DisplayName("포트는 인터페이스여야 한다")
    void ports_should_be_interfaces() {
        classes()
                .that().resideInAPackage("..domain.port..")
                .and().areTopLevelClasses()
                .and().doNotHaveSimpleName("package-info")
                .should().beInterfaces()
                .because("포트는 인터페이스로 정의되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("어댑터는 포트를 구현해야 한다")
    void adapters_should_implement_ports() {
        classes()
                .that().resideInAPackage("..infrastructure..")
                .and().haveSimpleNameEndingWith("Adapter")
                .should().implement(com.tngtech.archunit.core.domain.JavaClass.Predicates
                        .resideInAPackage("..domain.port.."))
                .because("어댑터는 포트 인터페이스를 구현해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Repository 인터페이스는 포트에 있어야 한다")
    void repository_interfaces_should_be_ports() {
        classes()
                .that().haveSimpleNameEndingWith("Repository")
                .and().areInterfaces()
                .should().resideInAPackage("..domain.port.repository..")
                .because("Repository 인터페이스는 도메인 포트여야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Repository 구현체는 인프라스트럭처에 있어야 한다")
    void repository_implementations_should_be_in_infrastructure() {
        classes()
                .that().haveSimpleNameEndingWith("Repository")
                .and().areNotInterfaces()
                .and().doNotHaveSimpleName("EventStoreRepository") // JPA Repository는 예외
                .should().resideInAPackage("..infrastructure..")
                .because("Repository 구현체는 인프라스트럭처 계층에 있어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("애플리케이션 서비스는 도메인 서비스만 사용해야 한다")
    void application_services_should_only_use_domain_services() {
        classes()
                .that().resideInAPackage("..application..")
                .should().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "..application..",
                        "..domain..",
                        "java..",
                        "lombok..",
                        "org.springframework.stereotype..",
                        "org.springframework.context..",
                        "com.fasterxml.jackson.."
                )
                .because("애플리케이션 계층은 도메인과 표준 라이브러리만 사용해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("도메인 서비스는 인프라스트럭처에 의존하지 않아야 한다")
    void domain_services_should_not_depend_on_infrastructure() {
        noClasses()
                .that().resideInAPackage("..domain.service..")
                .should().dependOnClassesThat().resideInAPackage("..infrastructure..")
                .because("도메인 서비스는 인프라스트럭처에 의존하지 않아야 함")
                .check(classes);
    }

    @Test
    @DisplayName("이벤트는 애플리케이션 계층에 있어야 한다")
    void events_should_be_in_application_layer() {
        classes()
                .that().haveSimpleNameEndingWith("Event")
                .should().resideInAPackage("..application.event..")
                .because("이벤트는 애플리케이션 계층의 관심사임")
                .check(classes);
    }

    @Test
    @DisplayName("커맨드는 애플리케이션 계층에 있어야 한다")
    void commands_should_be_in_application_layer() {
        classes()
                .that().haveSimpleNameEndingWith("Command")
                .should().resideInAPackage("..application.command..")
                .because("커맨드는 애플리케이션 계층의 관심사임")
                .check(classes);
    }
}