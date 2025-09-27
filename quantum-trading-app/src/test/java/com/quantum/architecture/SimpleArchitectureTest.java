package com.quantum.architecture;

import com.tngtech.archunit.junit.AnalyzeClasses;
import com.tngtech.archunit.junit.ArchTest;
import com.tngtech.archunit.lang.ArchRule;
import org.springframework.stereotype.Controller;
import org.springframework.stereotype.Repository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.RestController;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.*;

/**
 * 간단한 아키텍처 규칙 검증
 *
 * 실제로 동작하는 기본적인 ArchUnit 테스트들
 */
@AnalyzeClasses(packages = "com.quantum")
public class SimpleArchitectureTest {

    // =================================
    // 1. 기본 명명 규칙
    // =================================

    @ArchTest
    static final ArchRule controllers_should_end_with_controller =
            classes().that().areAnnotatedWith(Controller.class)
                    .or().areAnnotatedWith(RestController.class)
                    .should().haveSimpleNameEndingWith("Controller")
                    .because("컨트롤러는 Controller로 끝나야 합니다");

    @ArchTest
    static final ArchRule services_should_end_with_service =
            classes().that().areAnnotatedWith(Service.class)
                    .should().haveSimpleNameEndingWith("Service")
                    .because("서비스는 Service로 끝나야 합니다");

    @ArchTest
    static final ArchRule repositories_should_end_with_repository =
            classes().that().areAnnotatedWith(Repository.class)
                    .should().haveSimpleNameEndingWith("Repository")
                    .because("리포지토리는 Repository로 끝나야 합니다");

    // =================================
    // 2. 패키지 의존성 규칙
    // =================================

    @ArchTest
    static final ArchRule services_should_not_depend_on_controllers =
            classes().that().resideInAnyPackage("..service..")
                    .should().onlyDependOnClassesThat()
                    .resideOutsideOfPackages("..controller..")
                    .because("서비스는 컨트롤러에 의존하면 안됩니다");

    @ArchTest
    static final ArchRule domain_should_not_depend_on_infrastructure =
            classes().that().resideInAnyPackage("..domain..")
                    .should().onlyDependOnClassesThat()
                    .resideInAnyPackage("java..", "..domain..", "lombok..")
                    .because("도메인은 인프라에 의존하면 안됩니다 (Lombok 허용)");

    // =================================
    // 3. 어노테이션 규칙
    // =================================

    @ArchTest
    static final ArchRule services_should_be_transactional =
            classes().that().resideInAnyPackage("..application.service..")
                    .and().areAnnotatedWith(Service.class)
                    .should().beAnnotatedWith(Transactional.class)
                    .because("애플리케이션 서비스는 @Transactional이 필요합니다");

    @ArchTest
    static final ArchRule controllers_should_be_in_controller_packages =
            classes().that().areAnnotatedWith(Controller.class)
                    .or().areAnnotatedWith(RestController.class)
                    .should().resideInAnyPackage("..controller..", "..infrastructure.adapter.in.web..")
                    .because("컨트롤러는 컨트롤러 패키지에 있어야 합니다");

    // =================================
    // 4. 헥사고날 아키텍처 기본 규칙
    // =================================

    @ArchTest
    static final ArchRule use_cases_should_be_interfaces =
            classes().that().resideInAnyPackage("..application.port.in..")
                    .and().haveSimpleNameEndingWith("UseCase")
                    .should().beInterfaces()
                    .because("UseCase는 인터페이스여야 합니다");

    @ArchTest
    static final ArchRule ports_should_be_interfaces =
            classes().that().resideInAnyPackage("..application.port.out..")
                    .and().haveSimpleNameEndingWith("Port")
                    .should().beInterfaces()
                    .because("아웃바운드 포트는 인터페이스여야 합니다");

    // =================================
    // 5. 도메인 모듈 격리
    // =================================

    @ArchTest
    static final ArchRule kis_module_should_be_independent =
            classes().that().resideInAPackage("com.quantum.kis..")
                    .should().onlyDependOnClassesThat()
                    .resideInAnyPackage("java..", "org.springframework..", "org.slf4j..", "com.quantum.kis..",
                                      "com.fasterxml.jackson..", "jakarta.persistence..", "lombok..", "com.quantum.shared..")
                    .because("KIS 모듈은 독립적이어야 합니다 (JSON 처리와 JPA, 공통 인터페이스를 위한 제한적 의존성 허용)");

    @ArchTest
    static final ArchRule backtest_module_should_be_independent =
            classes().that().resideInAPackage("com.quantum.backtest..")
                    .should().onlyDependOnClassesThat()
                    .resideInAnyPackage("java..", "org.springframework..", "org.slf4j..", "com.quantum.backtest..",
                                      "com.fasterxml.jackson..", "jakarta.persistence..", "lombok..", "com.quantum.shared..")
                    .because("Backtest 모듈은 다른 비즈니스 모듈에 의존하면 안됩니다 (공통 인터페이스와 기술적 의존성 허용)");

    // =================================
    // 6. DTO 규칙
    // =================================

    @ArchTest
    static final ArchRule dto_classes_should_be_records =
            classes().that().resideInAnyPackage("..dto..")
                    .and().haveSimpleNameEndingWith("Result")
                    .should().beRecords()
                    .because("DTO Result 클래스는 record여야 합니다");

    @ArchTest
    static final ArchRule dto_should_not_depend_on_services =
            classes().that().resideInAnyPackage("..dto..")
                    .should().onlyDependOnClassesThat()
                    .resideOutsideOfPackages("..service..", "..application.service..", "..controller..")
                    .because("DTO는 서비스나 컨트롤러에 의존하면 안됩니다");
}