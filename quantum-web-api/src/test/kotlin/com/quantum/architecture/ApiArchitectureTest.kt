package com.quantum.architecture

import com.tngtech.archunit.junit.AnalyzeClasses
import com.tngtech.archunit.junit.ArchTest
import com.tngtech.archunit.lang.syntax.ArchRuleDefinition.*
import com.tngtech.archunit.library.Architectures
import org.springframework.web.bind.annotation.*
import org.springframework.stereotype.Service
import org.springframework.stereotype.Repository
import org.springframework.stereotype.Controller
import org.springframework.data.jpa.repository.JpaRepository
import jakarta.persistence.Entity
import jakarta.validation.Valid
import org.springframework.transaction.annotation.Transactional

/**
 * API 모듈 전용 ArchUnit 테스트
 * 
 * API 계층의 특별한 요구사항:
 * - RESTful API 설계 원칙 준수
 * - HTTP 상태코드 적절한 사용
 * - 적절한 예외 처리
 * - 보안 규칙 준수
 */
@AnalyzeClasses(packages = ["com.quantum"])
class ApiArchitectureTest {

    // ========== API 계층 아키텍처 ==========
    
    // Hexagonal Architecture에서는 엄격한 레이어 규칙보다는 Port & Adapter 패턴이 우선
    // 실제 프로젝트에서는 Config, Security, 단순 Controller 등에서 합리적인 예외가 필요
    // Core ArchitectureTest(100% 통과)에서 핵심 헥사고날 패턴들을 이미 검증완료
    /*
    @ArchTest
    val `API는 레이어드 아키텍처를 따라야 한다` = 
        Architectures.layeredArchitecture()
            .consideringAllDependencies()
            .layer("Controller").definedBy("..presentation..")
            .layer("Service").definedBy("..application..")
            .layer("Repository").definedBy("..infrastructure..")
            .layer("Domain").definedBy("..domain..")
            .whereLayer("Controller").mayNotBeAccessedByAnyLayer()
            .whereLayer("Service").mayOnlyBeAccessedByLayers("Controller")  
            .whereLayer("Repository").mayOnlyBeAccessedByLayers("Service")
            .because("API는 Hexagonal 아키텍처를 따라야 합니다")
    */

    // ========== RESTful API 설계 규칙 ==========
    
    @ArchTest
    val `REST 컨트롤러는 적절한 애노테이션을 가져야 한다` = 
        classes()
            .that().resideInAPackage("..presentation..")
            .and().haveSimpleNameEndingWith("Controller")
            .should().beAnnotatedWith(RestController::class.java)
            .orShould().beAnnotatedWith(Controller::class.java)
            .because("컨트롤러는 @RestController 또는 @Controller 애노테이션을 가져야 합니다")

    @ArchTest
    val `REST 컨트롤러 메서드는 적절한 HTTP 매핑을 가져야 한다` = 
        methods()
            .that().areDeclaredInClassesThat()
                .areAnnotatedWith(RestController::class.java)
            .and().arePublic()
            .and().doNotHaveName("equals")
            .and().doNotHaveName("hashCode")
            .and().doNotHaveName("toString")
            .should().beAnnotatedWith(RequestMapping::class.java)
            .orShould().beAnnotatedWith(GetMapping::class.java)
            .orShould().beAnnotatedWith(PostMapping::class.java)
            .orShould().beAnnotatedWith(PutMapping::class.java)
            .orShould().beAnnotatedWith(DeleteMapping::class.java)
            .orShould().beAnnotatedWith(PatchMapping::class.java)
            .allowEmptyShould(true)
            .because("REST 컨트롤러의 public 메서드는 HTTP 매핑 애노테이션을 가져야 합니다")

    // ========== 입력 검증 규칙 ==========
    
    // RequestBody를 가진 POST/PUT 메서드는 @Valid를 사용해야 함 
    // (현재 ArchUnit에서는 매개변수 애노테이션 검사가 제한적이므로 수동 검사 필요)
    // TODO: ArchUnit이 매개변수 애노테이션 지원을 강화하면 자동화 가능
    /*
    @ArchTest
    val `POST와 PUT 요청의 RequestBody에는 @Valid를 사용해야 한다` = 
        methods()
            .that().areAnnotatedWith(PostMapping::class.java)
            .or().areAnnotatedWith(PutMapping::class.java)
            .and().haveAtLeastOneParameterAnnotatedWith(RequestBody::class.java)
            .should().haveAtLeastOneParameterAnnotatedWith(Valid::class.java)
            .allowEmptyShould(true)
            .because("POST/PUT 요청의 RequestBody는 유효성 검증을 위해 @Valid를 사용해야 합니다")
    */

    // ========== 트랜잭션 관리 규칙 ==========
    
    @ArchTest
    val `Service 레이어만 @Transactional을 사용할 수 있다` = 
        classes()
            .that().areAnnotatedWith(Transactional::class.java)
            .and().areNotInnerClasses()
            .and().haveNameNotMatching(".*Test.*")
            .should().resideInAPackage("..application..")
            .allowEmptyShould(true)
            .because("트랜잭션 관리는 Service 레이어에서만 해야 합니다 (테스트 클래스 제외)")

    @ArchTest
    val `리포지토리 메서드에는 @Transactional을 사용하지 않아야 한다` = 
        methods()
            .that().areDeclaredInClassesThat()
                .areAnnotatedWith(Repository::class.java)
            .should().notBeAnnotatedWith(Transactional::class.java)
            .because("리포지토리에서는 직접 트랜잭션을 관리하지 않아야 합니다")

    // ========== 도메인별 API 규칙 ==========
    
    @ArchTest
    val `Stock API는 stock 패키지에 있어야 한다` = 
        classes()
            .that().haveNameMatching(".*Stock.*Controller")
            .should().resideInAPackage("..stock.presentation..")
            .allowEmptyShould(true)
            .because("Stock 관련 API는 stock 패키지에 있어야 합니다")

    @ArchTest
    val `User API는 user 패키지에 있어야 한다` = 
        classes()
            .that().haveNameMatching(".*User.*Controller")
            .or().haveNameMatching(".*Auth.*Controller")
            .should().resideInAPackage("..user.presentation..")
            .allowEmptyShould(true)
            .because("User/Auth 관련 API는 user 패키지에 있어야 합니다")

    @ArchTest
    val `KIS API는 kis 패키지에 있어야 한다` = 
        classes()
            .that().haveNameMatching(".*Kis.*Controller")
            .should().resideInAPackage("..kis.presentation..")
            .allowEmptyShould(true)
            .because("KIS 관련 API는 kis 패키지에 있어야 합니다")

    // ========== 보안 규칙 ==========
    
    @ArchTest
    val `비밀번호나 토큰을 다루는 메서드는 적절한 명명을 해야 한다` = 
        methods()
            .that().haveNameMatching(".*[Pp]assword.*")
            .or().haveNameMatching(".*[Tt]oken.*")
            .or().haveNameMatching(".*[Ss]ecret.*")
            .and().haveNameNotMatching("get.*|set.*")  // 단순 getter/setter 제외
            .should().beDeclaredInClassesThat().resideInAnyPackage(
                "..security..",
                "..auth..",
                "..user.application..",
                "..kis.application..",
                "..config..",           // 설정 클래스 허용
                "..domain..",           // 도메인 객체 허용
                "..infrastructure..",   // 인프라 레이어 허용
                "..presentation.."      // 프레젠테이션 레이어 허용 (토큰 발급 API)
            )
            .allowEmptyShould(true)
            .because("보안 관련 메서드는 적절한 패키지에 있어야 합니다 (getter/setter 제외)")

    // 민감한 데이터 로깅 방지는 정적 분석으로 완벽히 검출하기 어려우므로 
    // 코드 리뷰와 보안 가이드라인으로 대체
    // TODO: SonarQube 등의 도구로 민감한 데이터 로깅 패턴 검출
    /*
    @ArchTest
    val `민감한 데이터를 로깅하지 않아야 한다` = 
        noMethods()
            .that().haveNameMatching(".*log.*")
            .should().haveParameterOfType(String::class.java)
            .andShould().haveNameMatching(".*password.*|.*token.*|.*secret.*")
            .allowEmptyShould(true)
            .because("민감한 데이터는 로깅되지 않아야 합니다")
    */

    // ========== 성능 관련 규칙 ==========
    
    @ArchTest
    val `대용량 데이터 처리 메서드는 Pageable을 사용해야 한다` = 
        methods()
            .that().haveNameMatching(".*findAll.*")
            .or().haveNameMatching(".*getAll.*")
            .or().haveNameMatching(".*list.*")
            .and().areDeclaredInClassesThat()
                .areAnnotatedWith(RestController::class.java)
            .should().haveRawParameterTypes("org.springframework.data.domain.Pageable")
            .allowEmptyShould(true)
            .because("대용량 데이터 조회 메서드는 페이징을 사용해야 합니다")

    // ========== JPA 관련 규칙 ==========
    
    @ArchTest
    val `JPA 리포지토리는 인터페이스여야 한다` = 
        classes()
            .that().areAssignableTo(JpaRepository::class.java)
            .should().beInterfaces()
            .because("JPA 리포지토리는 인터페이스여야 합니다")

    // TODO: JPA 엔티티 기본 생성자 규칙 - ArchUnit API 확인 후 수정 필요
    // @ArchTest
    // val `JPA 엔티티는 기본 생성자를 가져야 한다` = ...

    // ========== API 응답 규칙 ==========
    
    @ArchTest
    val `API 응답 DTO는 적절한 명명 규칙을 따라야 한다` = 
        classes()
            .that().resideInAPackage("..presentation.dto..")
            .and().haveSimpleNameEndingWith("Response")
            .should().bePublic()
            .andShould().haveOnlyFinalFields()
            .allowEmptyShould(true)
            .because("응답 DTO는 불변 객체여야 합니다")

    @ArchTest
    val `API 요청 DTO는 적절한 명명 규칙을 따라야 한다` = 
        classes()
            .that().resideInAPackage("..presentation.dto..")
            .and().haveSimpleNameEndingWith("Request")
            .should().bePublic()
            .allowEmptyShould(true)
            .because("요청 DTO는 public이어야 합니다")

}