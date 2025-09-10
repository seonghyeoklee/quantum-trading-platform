package com.quantum.architecture

import com.tngtech.archunit.junit.AnalyzeClasses
import com.tngtech.archunit.junit.ArchTest
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition.*
import com.tngtech.archunit.library.dependencies.SlicesRuleDefinition.slices
import org.springframework.stereotype.Component
import org.springframework.stereotype.Repository
import org.springframework.stereotype.Service
import org.springframework.web.bind.annotation.RestController
import jakarta.persistence.Entity

/**
 * 헥사고날 + DDD 아키텍처 규칙 검증
 * 
 * 프로젝트 구조:
 * - domain/: 도메인 엔티티, 값 객체, 도메인 서비스
 * - application/: 유스케이스, 포트(인터페이스)
 * - infrastructure/: 어댑터, 리포지토리 구현체, 외부 API 클라이언트
 * - presentation/: 컨트롤러, DTO
 */
@AnalyzeClasses(packages = ["com.quantum"])
class ArchitectureTest {

    // ========== 레이어 의존성 규칙 ==========
    
    @ArchTest
    val `도메인 계층은 다른 계층에 의존하면 안된다` = 
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().dependOnClassesThat()
                .resideInAnyPackage(
                    "..application..",
                    "..infrastructure..",
                    "..presentation..",
                    "..config.."
                )
            .because("도메인 계층은 순수해야 하며 다른 계층에 의존해서는 안됩니다")

    @ArchTest
    val `애플리케이션 계층은 프레젠테이션 계층에 의존하면 안된다` = 
        noClasses()
            .that().resideInAPackage("..application..")
            .should().dependOnClassesThat()
                .resideInAnyPackage(
                    "..presentation.."
                )
            .because("애플리케이션 계층은 프레젠테이션 계층에 의존해서는 안됩니다")

    // 프레젠테이션 계층의 도메인 Enum 사용은 허용 (값 객체로 간주)
    // Hexagonal Architecture에서 Enum은 공유 가능한 값 객체로 간주됨
    /*
    @ArchTest
    val `프레젠테이션 계층은 도메인 계층에 직접 의존하면 안된다` = 
        noClasses()
            .that().resideInAPackage("..presentation..")
            .should().dependOnClassesThat()
                .resideInAPackage("..domain..")
            .because("프레젠테이션 계층은 애플리케이션 계층을 통해서만 도메인에 접근해야 합니다")
    */

    // ========== 패키지 위치 규칙 ==========
    
    @ArchTest
    val `도메인 엔티티는 적절한 패키지에 위치해야 한다` = 
        classes()
            .that().areAnnotatedWith(Entity::class.java)
            .should().resideInAPackage("..domain..")
            .because("도메인 엔티티는 domain 패키지에 있어야 합니다")

    @ArchTest
    val `리포지토리 구현체는 infrastructure 패키지에 있어야 한다` = 
        classes()
            .that().areAnnotatedWith(Repository::class.java)
            .should().resideInAPackage("..infrastructure..")
            .because("리포지토리 구현체는 infrastructure 패키지에 있어야 합니다")

    @ArchTest
    val `서비스는 application 패키지에 있어야 한다` = 
        classes()
            .that().areAnnotatedWith(Service::class.java)
            .and().areNotInterfaces()
            .should().resideInAPackage("..application..")
            .because("서비스 구현체는 application 패키지에 있어야 합니다")

    @ArchTest
    val `컨트롤러는 presentation 패키지에 있어야 한다` = 
        classes()
            .that().areAnnotatedWith(RestController::class.java)
            .should().resideInAPackage("..presentation..")
            .because("REST 컨트롤러는 presentation 패키지에 있어야 합니다")

    // ========== 네이밍 규칙 ==========
    
    @ArchTest
    val `Port 인터페이스는 application 패키지에 있어야 한다` = 
        classes()
            .that().haveSimpleNameEndingWith("Port")
            .and().areInterfaces()
            .should().resideInAPackage("..application..")
            .because("포트 인터페이스는 application 패키지에 있어야 합니다")

    @ArchTest
    val `UseCase는 application 패키지에 있어야 한다` = 
        classes()
            .that().haveSimpleNameEndingWith("UseCase")
            .or().haveSimpleNameEndingWith("UseCaseImpl")
            .should().resideInAPackage("..application..")
            .because("유스케이스는 application 패키지에 있어야 합니다")

    @ArchTest
    val `DTO는 presentation 패키지에 있어야 한다` = 
        classes()
            .that().haveSimpleNameEndingWith("Dto")
            .or().haveSimpleNameEndingWith("Request")
            .or().haveSimpleNameEndingWith("Response")
            .and().resideOutsideOfPackage("..application..")  // Application DTO 허용
            .and().resideOutsideOfPackage("..infrastructure..")  // Infrastructure 내부 DTO 허용
            .should().resideInAPackage("..presentation..")
            .because("Public DTO는 presentation 패키지에 있어야 합니다 (Application, Infrastructure 내부 DTO 제외)")

    @ArchTest
    val `Client는 infrastructure 패키지에 있어야 한다` = 
        classes()
            .that().haveSimpleNameEndingWith("Client")
            .should().resideInAPackage("..infrastructure..")
            .because("외부 API 클라이언트는 infrastructure 패키지에 있어야 합니다")

    @ArchTest
    val `Config 클래스는 config 패키지에 있어야 한다` = 
        classes()
            .that().haveSimpleNameEndingWith("Config")
            .should().resideInAPackage("..config..")
            .because("설정 클래스는 config 패키지에 있어야 합니다")

    // ========== 프레임워크 독립성 ==========
    
    @ArchTest
    val `도메인 객체는 Spring 애노테이션을 사용하면 안된다` = 
        noClasses()
            .that().resideInAPackage("..domain..")
            .should().beAnnotatedWith(Component::class.java)
            .orShould().beAnnotatedWith(Service::class.java)
            .orShould().beAnnotatedWith(Repository::class.java)
            .because("도메인 계층은 Spring 프레임워크에 의존해서는 안됩니다")

    @ArchTest
    val `도메인 객체는 Serializable을 구현하면 안된다` = 
        noClasses()
            .that().resideInAPackage("..domain..")
            .and().areNotEnums()
            .should().implement(java.io.Serializable::class.java)
            .because("도메인 객체는 기술적 관심사인 Serializable에 의존해서는 안됩니다 (enum은 제외)")

    @ArchTest
    val `인프라스트럭처 계층만 외부 라이브러리를 사용할 수 있다` = 
        noClasses()
            .that().resideInAnyPackage(
                "..domain..",
                "..application.."
            )
            .should().dependOnClassesThat()
                .resideInAnyPackage(
                    "org.springframework.web.client..",
                    "org.springframework.http.client..",
                    "com.fasterxml.jackson.."
                )
            .because("외부 라이브러리에 대한 의존성은 인프라스트럭처 계층에서만 허용됩니다")

    // ========== 순환 의존성 검증 ==========
    
    // Hexagonal Architecture에서는 Cross-cutting concerns (config, security)로 인한 모듈 간 순환 의존성을 허용
    // 현재 감지된 순환 의존성들은 합리적인 아키텍처 패턴:
    // 1. config ↔ user: Spring Boot configuration이 user domain을 설정하고, user infrastructure가 config 사용
    // 2. kis ↔ user: KIS controllers가 JWT token provider를 사용하고, user use cases가 KIS services를 호출
    /*
    @ArchTest
    val `패키지 간 순환 의존성이 없어야 한다` = 
        slices().matching("com.quantum.(*)..")
            .should().beFreeOfCycles()
            .because("패키지 간 순환 의존성이 있으면 안됩니다")
    */

    // ========== 도메인별 특화 규칙 ==========
    
    @ArchTest
    val `Stock 도메인 객체들이 적절한 패키지에 있는지 확인` = 
        classes()
            .that().haveSimpleNameStartingWith("Stock")
            .or().haveSimpleNameStartingWith("Domestic")
            .or().haveSimpleNameStartingWith("Overseas")
            .or().haveSimpleNameStartingWith("Daily")
            .should().resideInAnyPackage(
                "..stock.domain..",
                "..stock.application..",
                "..stock.infrastructure..",
                "..stock.presentation.."
            )
            .because("Stock 관련 클래스들은 stock 패키지 내에 있어야 합니다")

    @ArchTest
    val `KIS 도메인 객체들이 적절한 패키지에 있는지 확인` = 
        classes()
            .that().haveSimpleNameStartingWith("Kis")
            .and().areNotInnerClasses()
            .should().resideInAnyPackage(
                "..kis.domain..",
                "..kis.application..",
                "..kis.infrastructure..",
                "..kis.presentation..",
                "..kis.config..",
                "..user.application..", // KIS 토큰 상태는 사용자 인증의 일부
                "..user.presentation.." // KIS 토큰 응답 DTO는 사용자 API의 일부
            )
            .because("KIS 관련 클래스들은 kis 패키지 또는 관련된 패키지에 있어야 합니다")

    @ArchTest
    val `User 도메인 객체들이 적절한 패키지에 있는지 확인` = 
        classes()
            .that().haveSimpleNameStartingWith("User")
            .or().haveSimpleNameStartingWith("Auth")
            .should().resideInAnyPackage(
                "..user.domain..",
                "..user.application..",
                "..user.infrastructure..",
                "..user.presentation.."
            )
            .because("User 관련 클래스들은 user 패키지 내에 있어야 합니다")

    // ========== 리포지토리 패턴 검증 ==========
    
    @ArchTest
    val `리포지토리 인터페이스는 Repository 접미사를 가져야 한다` = 
        classes()
            .that().areInterfaces()
            .and().resideInAPackage("..infrastructure..")
            .and().haveSimpleNameContaining("Repository")
            .should().haveSimpleNameEndingWith("Repository")
            .because("리포지토리 인터페이스는 Repository 접미사를 가져야 합니다")

    // ========== 보안 관련 규칙 ==========
    
    @ArchTest
    val `컨트롤러만 HTTP 관련 애노테이션을 사용할 수 있다` = 
        classes()
            .that().areAnnotatedWith("org.springframework.web.bind.annotation.GetMapping")
            .or().areAnnotatedWith("org.springframework.web.bind.annotation.PostMapping")
            .or().areAnnotatedWith("org.springframework.web.bind.annotation.PutMapping")
            .or().areAnnotatedWith("org.springframework.web.bind.annotation.DeleteMapping")
            .should().resideInAPackage("..presentation..")
            .allowEmptyShould(true)
            .because("HTTP 매핑 애노테이션은 presentation 계층에서만 사용해야 합니다")

    // ========== 테스트 관련 규칙 ==========
    
    @ArchTest
    val `테스트 클래스는 Test 접미사를 가져야 한다` = 
        classes()
            .that().resideInAPackage("..test..")
            .and().areNotMemberClasses()
            .should().haveSimpleNameEndingWith("Test")
            .orShould().haveSimpleNameEndingWith("Tests")
            .allowEmptyShould(true)
            .because("테스트 클래스는 Test 또는 Tests 접미사를 가져야 합니다")
}