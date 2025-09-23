package com.quantum.kis.exception;

/**
 * KIS API 호출 시 발생하는 예외
 */
public class KisApiException extends RuntimeException {
    private final String errorCode;

    public KisApiException(String message) {
        super(message);
        this.errorCode = null;
    }

    public KisApiException(String message, Throwable cause) {
        super(message, cause);
        this.errorCode = null;
    }

    public KisApiException(String message, String errorCode) {
        super(message);
        this.errorCode = errorCode;
    }

    public KisApiException(String message, Throwable cause, String errorCode) {
        super(message, cause);
        this.errorCode = errorCode;
    }

    public String getErrorCode() {
        return errorCode;
    }
}