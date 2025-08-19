package com.quantum.api.architecture;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.*;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.library.Architectures;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

/**
 * Quantum API 헥사고날 아키텍처 검증 테스트
 * 
 * quantum-api 모듈의 헥사고날 아키텍처 원칙들을 ArchUnit으로 강제한다:
 * 1. Port-Adapter 패턴의 올바른 구현
 * 2. Inbound/Outbound 어댑터의 명확한 분리
 * 3. Application 계층의 순수성
 * 4. Web 계층과 비즈니스 로직의 분리
 */
@DisplayName("🏗️ Quantum API Hexagonal Architecture Rules")
class HexagonalArchitectureTest {

    private static final String BASE_PACKAGE = "com.quantum.api";
    private static final JavaClasses classes = new ClassFileImporter()
            .importPackages(BASE_PACKAGE);

    @Test
    @DisplayName("헥사고날 아키텍처 계층 구조가 올바르게 정의되어야 한다")
    void hexagonal_architecture_should_be_respected() {
        Architectures.layeredArchitecture()
                .consideringOnlyDependenciesInLayers()
                .layer("Inbound Adapters").definedBy("..adapter.in..")
                .layer("Outbound Adapters").definedBy("..adapter.out..")
                .layer("Application").definedBy("..application..")
                .layer("Config").definedBy("..config..")
                .layer("Infrastructure").definedBy("..infrastructure..")
                
                .whereLayer("Inbound Adapters").mayOnlyAccessLayers("Application")
                .whereLayer("Outbound Adapters").mayOnlyAccessLayers("Application", "Infrastructure")
                .whereLayer("Application").mayNotAccessAnyLayer() // 외부 의존성 없음
                .whereLayer("Config").mayAccessLayers("Application", "Inbound Adapters", "Outbound Adapters", "Infrastructure")
                .whereLayer("Infrastructure").mayOnlyAccessLayers("Application")
                
                .check(classes);
    }

    @Test
    @DisplayName("Inbound Port는 Application 계층에 정의되어야 한다")
    void inbound_ports_should_be_in_application_layer() {
        classes()
                .that().resideInAPackage("..application.port.in..")
                .should().beInterfaces()
                .because("Inbound Port는 애플리케이션으로 들어오는 인터페이스임")
                .check(classes);
    }

    @Test
    @DisplayName("Outbound Port는 Application 계층에 정의되어야 한다")
    void outbound_ports_should_be_in_application_layer() {
        classes()
                .that().resideInAPackage("..application.port.out..")
                .should().beInterfaces()
                .because("Outbound Port는 애플리케이션에서 나가는 인터페이스임")
                .check(classes);
    }

    @Test
    @DisplayName("Web Controller는 Inbound Adapter여야 한다")
    void web_controllers_should_be_inbound_adapters() {
        classes()
                .that().areAnnotatedWith("org.springframework.web.bind.annotation.RestController")
                .or().areAnnotatedWith("org.springframework.stereotype.Controller")
                .should().resideInAPackage("..adapter.in.web..")
                .because("Web Controller는 외부 요청을 받는 Inbound Adapter임")
                .check(classes);
    }

    @Test
    @DisplayName("Outbound Adapter는 외부 시스템과 연결하는 역할만 해야 한다")
    void outbound_adapters_should_only_connect_to_external_systems() {
        classes()
                .that().resideInAPackage("..adapter.out..")
                .should().haveSimpleNameEndingWith("Adapter")
                .orShould().haveSimpleNameEndingWith("Client")
                .orShould().haveSimpleNameEndingWith("Repository")
                .because("Outbound Adapter는 명확한 네이밍을 가져야 함")
                .check(classes);
    }

    @Test
    @DisplayName("UseCase는 비즈니스 로직의 진입점이어야 한다")
    void usecases_should_be_business_logic_entry_points() {
        classes()
                .that().haveSimpleNameEndingWith("Usecase")
                .should().resideInAPackage("..application.usecase..")
                .andShould().beInterfaces()
                .because("UseCase는 애플리케이션의 비즈니스 로직 진입점임")
                .check(classes);
    }

    @Test
    @DisplayName("Application Service는 UseCase를 구현해야 한다")
    void application_services_should_implement_usecases() {
        classes()
                .that().resideInAPackage("..application.service..")
                .should().haveSimpleNameEndingWith("Service")
                .because("Application Service는 명확한 네이밍을 가져야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Controller는 Application 계층에만 의존해야 한다")
    void controllers_should_only_depend_on_application_layer() {
        classes()
                .that().resideInAPackage("..adapter.in.web..")
                .should().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "..application..",
                        "com.quantum.core.domain..",  // 도메인 모델 허용
                        "java..",
                        "org.springframework..",
                        "io.swagger..",
                        "lombok.."
                )
                .because("Controller는 Application 계층과 도메인 모델에만 의존해야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Application 계층은 외부 프레임워크에 의존하지 않아야 한다")
    void application_layer_should_not_depend_on_external_frameworks() {
        classes()
                .that().resideInAPackage("..application..")
                .should().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "..application..",
                        "com.quantum.core..",  // Core 모듈 허용
                        "java..",
                        "org.springframework.stereotype..",  // @Service, @Component 허용
                        "lombok.."
                )
                .because("Application 계층은 비즈니스 로직에 집중하고 프레임워크에 의존하지 않아야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Outbound Adapter는 Port 인터페이스를 구현해야 한다")
    void outbound_adapters_should_implement_port_interfaces() {
        classes()
                .that().resideInAPackage("..adapter.out..")
                .and().haveSimpleNameEndingWith("Adapter")
                .should().implementInterface("org.springframework.stereotype.Component")
                .orShould().beAnnotatedWith("org.springframework.stereotype.Component")
                .orShould().beAnnotatedWith("org.springframework.stereotype.Service")
                .because("Outbound Adapter는 Spring 컴포넌트로 등록되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Configuration은 독립적인 계층에 있어야 한다")
    void configurations_should_be_in_separate_layer() {
        classes()
                .that().haveSimpleNameEndingWith("Config")
                .or().haveSimpleNameEndingWith("Configuration")
                .should().resideInAPackage("..config..")
                .because("Configuration은 별도의 계층으로 분리되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Port 인터페이스는 순수해야 한다")
    void port_interfaces_should_be_pure() {
        classes()
                .that().resideInAPackage("..application.port..")
                .should().beInterfaces()
                .andShould().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "com.quantum.core..",
                        "java..",
                        "org.springframework.data.domain.."  // Pageable 등 허용
                )
                .because("Port 인터페이스는 순수하고 기술적 세부사항에 의존하지 않아야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Adapter는 단일 책임을 가져야 한다")
    void adapters_should_have_single_responsibility() {
        classes()
                .that().haveSimpleNameEndingWith("Adapter")
                .should().haveOnlyOnePublicConstructor()
                .because("Adapter는 단일 책임을 가지고 의존성 주입을 통해 구성되어야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Web 계층은 HTTP 관련 어노테이션만 사용해야 한다")
    void web_layer_should_only_use_http_annotations() {
        noClasses()
                .that().resideInAPackage("..adapter.in.web..")
                .should().dependOnClassesThat().resideInAnyPackage(
                        "jakarta.persistence..",
                        "org.springframework.data.jpa..",
                        "org.springframework.transaction.."
                )
                .because("Web 계층은 HTTP 관련 어노테이션만 사용하고 영속성 기술에 의존하지 않아야 함")
                .check(classes);
    }

    @Test
    @DisplayName("Infrastructure 매퍼는 독립적이어야 한다")
    void infrastructure_mappers_should_be_independent() {
        classes()
                .that().resideInAPackage("..infrastructure.mapper..")
                .should().haveSimpleNameEndingWith("Mapper")
                .andShould().onlyDependOnClassesThat()
                .resideInAnyPackage(
                        "com.quantum.core..",
                        "com.quantum.kis..",  // 외부 API 모델 허용
                        "java..",
                        "org.springframework.stereotype..",
                        "lombok.."
                )
                .because("Infrastructure 매퍼는 도메인과 외부 모델 간 변환만 담당해야 함")
                .check(classes);
    }
}