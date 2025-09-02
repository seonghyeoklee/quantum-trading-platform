package com.quantum.user.application.port.outgoing

/**
 * 비밀번호 인코딩 포트
 */
interface PasswordEncodingPort {
    
    /**
     * 비밀번호 암호화
     */
    fun encode(rawPassword: String): String
    
    /**
     * 비밀번호 검증
     */
    fun matches(rawPassword: String, encodedPassword: String): Boolean
}