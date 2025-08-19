package com.quantum.core.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.*;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * 기본 아키텍처 규칙 검증 테스트
 * 
 * 핵심적인 아키텍처 원칙들을 ArchUnit으로 검증한다:
 * 1. 모듈간 의존성 방향
 * 2. 계층간 의존성 제한
 * 3. 네이밍 규약
 */
@DisplayName("🏗️ Basic Architecture Rules")
class SimpleArchitectureTest {

    private static final String BASE_PACKAGE = "com.quantum.core";
    private static final JavaClasses classes = new ClassFileImporter()
            .importPackages(BASE_PACKAGE);

    @Test
    @DisplayName("도메인 계층은 인프라스트럭처 계층에 의존하지 않아야 한다")
    void domain_should_not_depend_on_infrastructure() {
        noClasses()
                .that().resideInAPackage("..domain..")
                .should().dependOnClassesThat().resideInAPackage("..infrastructure..")
                .because("도메인 계층은 인프라스트럭처에 의존하지 않아야 함")
                .check(classes);
    }

    @Test
    @DisplayName("포트 인터페이스는 어댑터 구현체에 의존하지 않아야 한다")
    void ports_should_not_depend_on_adapters() {
        noClasses()
                .that().resideInAPackage("..domain.port..")
                .should().dependOnClassesThat().resideInAPackage("..infrastructure..")
                .because("포트는 어댑터에 의존하지 않아야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Repository 인터페이스는 domain.port.repository 패키지에 있어야 한다")
    void repository_interfaces_should_be_in_domain_ports() {
        classes()
                .that().haveSimpleNameEndingWith("Repository")
                .and().areInterfaces()
                .should().resideInAPackage("..domain.port.repository..")
                .because("Repository 인터페이스는 도메인 포트여야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Repository 구현체는 infrastructure 패키지에 있어야 한다")
    void repository_implementations_should_be_in_infrastructure() {
        classes()
                .that().haveSimpleNameEndingWith("RepositoryImpl")
                .or().haveSimpleNameEndingWith("RepositoryAdapter")
                .should().resideInAPackage("..infrastructure..")
                .because("Repository 구현체는 인프라스트럭처여야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Configuration은 Infrastructure 계층에만 있어야 한다")
    void configurations_should_be_in_infrastructure() {
        classes()
                .that().haveSimpleNameEndingWith("Config")
                .or().haveSimpleNameEndingWith("Configuration")
                .should().resideInAPackage("..infrastructure..")
                .because("설정은 인프라스트럭처의 관심사임")
                .check(classes);
    }

    @Test
    @DisplayName("Entity는 도메인 모델 패키지에 있어야 한다")
    void entities_should_be_in_domain_model_package() {
        classes()
                .that().areAnnotatedWith("jakarta.persistence.Entity")
                .should().resideInAPackage("..domain.model..")
                .because("Entity는 도메인 모델이어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Event는 application.event 패키지에 있어야 한다")
    void events_should_be_in_application_event_package() {
        classes()
                .that().haveSimpleNameEndingWith("Event")
                .should().resideInAPackage("..application.event..")
                .because("Event는 애플리케이션 이벤트여야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Command는 application.command 패키지에 있어야 한다")
    void commands_should_be_in_application_command_package() {
        classes()
                .that().haveSimpleNameEndingWith("Command")
                .should().resideInAPackage("..application.command..")
                .because("Command는 애플리케이션 명령이어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("State는 application.state 패키지에 있어야 한다")
    void states_should_be_in_application_state_package() {
        classes()
                .that().haveSimpleNameEndingWith("State")
                .should().resideInAPackage("..application.state..")
                .because("State는 애플리케이션 상태여야 함")
                .check(classes);
    }

    @Test
    @DisplayName("도메인 모델은 순수해야 한다")
    void domain_models_should_be_pure() {
        classes()
                .that().resideInAPackage("..domain.model..")
                .should().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "..domain..",
                        "java..",
                        "jakarta.persistence..",
                        "jakarta.validation..",
                        "lombok..",
                        "com.fasterxml.jackson.."
                )
                .because("도메인 모델은 순수해야 함")
                .check(classes);
    }
}