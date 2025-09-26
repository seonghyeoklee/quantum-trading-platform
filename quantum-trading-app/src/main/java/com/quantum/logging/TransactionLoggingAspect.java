package com.quantum.logging;

import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.*;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.stereotype.Component;

import java.util.Arrays;
import java.util.UUID;

/**
 * 트랜잭션 로깅 AOP Aspect
 * @Transactional이 적용된 메서드의 시작/종료를 로깅합니다.
 */
@Aspect
// @Component  // 트랜잭션 로깅 비활성화
public class TransactionLoggingAspect {

    private static final Logger log = LoggerFactory.getLogger("com.quantum.logging.TransactionLogger");

    private static final String TX_ID_KEY = "txId";
    private static final String TX_DEPTH_KEY = "txDepth";

    /**
     * @Transactional이 적용된 메서드 포인트컷 (Config 클래스 제외)
     */
    @Pointcut("(@annotation(org.springframework.transaction.annotation.Transactional) || " +
              "@within(org.springframework.transaction.annotation.Transactional)) && " +
              "!@within(org.springframework.boot.context.properties.ConfigurationProperties) && " +
              "!@within(org.springframework.context.annotation.Configuration) && " +
              "!within(com.quantum..config..*)")
    public void transactionalMethod() {}

    /**
     * KIS 패키지의 메서드 포인트컷 (Config 클래스 제외)
     */
    @Pointcut("execution(* com.quantum.kis..*(..)) && !within(com.quantum.kis.config..*)")
    public void kisPackage() {}

    /**
     * DINO 패키지의 메서드 포인트컷 (Config 클래스 제외)
     */
    @Pointcut("execution(* com.quantum.dino..*(..)) && !within(com.quantum.dino.config..*)")
    public void dinoPackage() {}

    /**
     * 트랜잭션 메서드 실행 로깅
     */
    @Around("transactionalMethod()")
    public Object logTransaction(ProceedingJoinPoint joinPoint) throws Throwable {
        String txId = generateTransactionId();
        String methodName = joinPoint.getSignature().toShortString();
        Object[] args = joinPoint.getArgs();

        // 현재 트랜잭션 깊이 확인
        int currentDepth = getCurrentDepth();
        int newDepth = currentDepth + 1;

        // MDC에 트랜잭션 정보 설정
        String previousTxId = MDC.get(TX_ID_KEY);
        MDC.put(TX_ID_KEY, txId);
        MDC.put(TX_DEPTH_KEY, String.valueOf(newDepth));

        String indent = getIndent(newDepth);

        try {
            // 트랜잭션 시작 로깅
            log.info("{}🔄 TX-START [{}] {} with args: {}",
                    indent, txId, methodName, formatArgs(args));

            long startTime = System.currentTimeMillis();

            // 메서드 실행
            Object result = joinPoint.proceed();

            long executionTime = System.currentTimeMillis() - startTime;

            // 트랜잭션 성공 로깅
            log.info("{}✅ TX-SUCCESS [{}] {} ({}ms)",
                    indent, txId, methodName, executionTime);

            return result;

        } catch (Exception e) {
            // 트랜잭션 실패 로깅
            log.error("{}❌ TX-FAILURE [{}] {} - Error: {}",
                    indent, txId, methodName, e.getMessage());
            throw e;

        } finally {
            // MDC 정리
            if (previousTxId != null) {
                MDC.put(TX_ID_KEY, previousTxId);
                MDC.put(TX_DEPTH_KEY, String.valueOf(currentDepth));
            } else {
                MDC.remove(TX_ID_KEY);
                MDC.remove(TX_DEPTH_KEY);
            }
        }
    }

    /**
     * KIS API 메서드 로깅
     */
    @Around("kisPackage()")
    public Object logKisMethod(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().toShortString();
        String className = joinPoint.getSignature().getDeclaringTypeName();
        Object[] args = joinPoint.getArgs();

        // KIS 관련 메서드는 특별한 아이콘으로 구분
        String icon = getKisMethodIcon(className, methodName);

        log.debug("{}🚀 KIS-CALL: {} with args: {}", icon, methodName, formatArgs(args));

        long startTime = System.currentTimeMillis();

        try {
            Object result = joinPoint.proceed();
            long executionTime = System.currentTimeMillis() - startTime;

            log.debug("{}✅ KIS-SUCCESS: {} ({}ms)", icon, methodName, executionTime);
            return result;

        } catch (Exception e) {
            long executionTime = System.currentTimeMillis() - startTime;
            log.error("{}❌ KIS-FAILURE: {} ({}ms) - Error: {}",
                    icon, methodName, executionTime, e.getMessage());
            throw e;
        }
    }

    /**
     * DINO 분석 메서드 로깅
     */
    @Around("dinoPackage()")
    public Object logDinoMethod(ProceedingJoinPoint joinPoint) throws Throwable {
        String methodName = joinPoint.getSignature().toShortString();
        Object[] args = joinPoint.getArgs();

        log.debug("🧠 DINO-ANALYSIS: {} with args: {}", methodName, formatArgs(args));

        long startTime = System.currentTimeMillis();

        try {
            Object result = joinPoint.proceed();
            long executionTime = System.currentTimeMillis() - startTime;

            log.debug("📊 DINO-RESULT: {} ({}ms)", methodName, executionTime);
            return result;

        } catch (Exception e) {
            long executionTime = System.currentTimeMillis() - startTime;
            log.error("💥 DINO-ERROR: {} ({}ms) - Error: {}",
                    methodName, executionTime, e.getMessage());
            throw e;
        }
    }

    /**
     * 트랜잭션 ID 생성
     */
    private String generateTransactionId() {
        return UUID.randomUUID().toString().substring(0, 8);
    }

    /**
     * 현재 트랜잭션 깊이 확인
     */
    private int getCurrentDepth() {
        String depthStr = MDC.get(TX_DEPTH_KEY);
        return depthStr != null ? Integer.parseInt(depthStr) : 0;
    }

    /**
     * 들여쓰기 생성
     */
    private String getIndent(int depth) {
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < depth; i++) {
            sb.append("  ");
        }
        return sb.toString();
    }

    /**
     * KIS 메서드별 아이콘 결정
     */
    private String getKisMethodIcon(String className, String methodName) {
        if (className.contains("Token")) {
            return "🔐";  // 토큰 관련
        } else if (methodName.contains("price") || methodName.contains("Price")) {
            return "📈";  // 가격 관련
        } else if (methodName.contains("order") || methodName.contains("Order")) {
            return "📋";  // 주문 관련
        } else if (methodName.contains("account") || methodName.contains("Account")) {
            return "💼";  // 계좌 관련
        } else {
            return "🌐";  // 일반 API
        }
    }

    /**
     * 인자값 포맷팅 (보안 정보 마스킹)
     */
    private String formatArgs(Object[] args) {
        if (args == null || args.length == 0) {
            return "[]";
        }

        return Arrays.stream(args)
                .map(arg -> {
                    if (arg == null) return "null";

                    String argStr = arg.toString();

                    // 토큰이나 시크릿 정보 마스킹
                    if (argStr.length() > 20 && (
                        argStr.contains("token") ||
                        argStr.contains("key") ||
                        argStr.contains("secret"))) {
                        return maskSensitiveData(argStr);
                    }

                    // 너무 긴 문자열은 자르기
                    if (argStr.length() > 100) {
                        return argStr.substring(0, 100) + "...";
                    }

                    return argStr;
                })
                .reduce((a, b) -> a + ", " + b)
                .map(s -> "[" + s + "]")
                .orElse("[]");
    }

    /**
     * 민감한 데이터 마스킹
     */
    private String maskSensitiveData(String data) {
        if (data.length() <= 8) {
            return "****";
        }
        return data.substring(0, 4) + "****" + data.substring(data.length() - 4);
    }
}