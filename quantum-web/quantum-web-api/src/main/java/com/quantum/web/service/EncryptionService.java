package com.quantum.web.service;

import com.quantum.trading.platform.shared.value.ApiCredentials;
import com.quantum.trading.platform.shared.value.EncryptedValue;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;
import java.nio.charset.StandardCharsets;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.util.Base64;

/**
 * AES-256-GCM 암호화 서비스
 * 
 * 키움증권 API credentials 등 민감한 정보를 안전하게 암호화/복호화
 * - AES-256-GCM 알고리즘 사용 (인증 암호화)
 * - 솔트 기반 키 유도
 * - 안전한 랜덤 IV 생성
 */
@Service
@Slf4j
public class EncryptionService {

    private static final String ALGORITHM = "AES";
    private static final String TRANSFORMATION = "AES/GCM/NoPadding";
    private static final int GCM_IV_LENGTH = 12; // 96 bits
    private static final int GCM_TAG_LENGTH = 16; // 128 bits
    private static final int SALT_LENGTH = 32; // 256 bits
    private static final int KEY_LENGTH = 256; // AES-256

    @Value("${quantum.encryption.master-key:DEFAULT_MASTER_KEY_CHANGE_IN_PRODUCTION}")
    private String masterKey;

    private final SecureRandom secureRandom = new SecureRandom();

    /**
     * API Credentials 암호화
     */
    public EncryptedValue encryptApiCredentials(ApiCredentials credentials) {
        try {
            log.debug("Encrypting API credentials for client ID: {}", 
                    maskString(credentials.getClientId(), 4));

            // 클라이언트 ID와 시크릿을 JSON 형태로 결합
            String credentialsJson = String.format(
                    "{\"clientId\":\"%s\",\"clientSecret\":\"%s\"}", 
                    credentials.getClientId(), 
                    credentials.getClientSecret()
            );

            return encrypt(credentialsJson);

        } catch (Exception e) {
            log.error("Failed to encrypt API credentials", e);
            throw new EncryptionException("Failed to encrypt API credentials", e);
        }
    }

    /**
     * API Credentials 복호화
     */
    public ApiCredentials decryptApiCredentials(EncryptedValue encryptedValue) {
        try {
            log.debug("Decrypting API credentials");

            String credentialsJson = decrypt(encryptedValue);

            // 간단한 JSON 파싱 (실제로는 Jackson 등 사용 권장)
            String clientId = extractJsonValue(credentialsJson, "clientId");
            String clientSecret = extractJsonValue(credentialsJson, "clientSecret");

            log.debug("Successfully decrypted API credentials for client ID: {}", 
                    maskString(clientId, 4));

            return ApiCredentials.of(clientId, clientSecret);

        } catch (Exception e) {
            log.error("Failed to decrypt API credentials", e);
            throw new EncryptionException("Failed to decrypt API credentials", e);
        }
    }

    /**
     * 일반 텍스트 암호화
     */
    public EncryptedValue encrypt(String plaintext) {
        try {
            // 1. 솔트 생성
            byte[] salt = generateSalt();

            // 2. 암호화 키 유도
            SecretKey key = deriveKey(salt);

            // 3. IV 생성
            byte[] iv = generateIV();

            // 4. 암호화 수행
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            GCMParameterSpec parameterSpec = new GCMParameterSpec(GCM_TAG_LENGTH * 8, iv);
            cipher.init(Cipher.ENCRYPT_MODE, key, parameterSpec);

            byte[] ciphertext = cipher.doFinal(plaintext.getBytes(StandardCharsets.UTF_8));

            // 5. IV + 암호문 결합
            byte[] encryptedData = new byte[iv.length + ciphertext.length];
            System.arraycopy(iv, 0, encryptedData, 0, iv.length);
            System.arraycopy(ciphertext, 0, encryptedData, iv.length, ciphertext.length);

            // 6. Base64 인코딩
            String encryptedDataBase64 = Base64.getEncoder().encodeToString(encryptedData);
            String saltBase64 = Base64.getEncoder().encodeToString(salt);

            log.debug("Successfully encrypted data with salt length: {} bytes", salt.length);

            return EncryptedValue.of(encryptedDataBase64, saltBase64);

        } catch (Exception e) {
            log.error("Failed to encrypt data", e);
            throw new EncryptionException("Encryption failed", e);
        }
    }

    /**
     * 일반 텍스트 복호화
     */
    public String decrypt(EncryptedValue encryptedValue) {
        try {
            // 1. Base64 디코딩
            byte[] encryptedData = Base64.getDecoder().decode(encryptedValue.getEncryptedData());
            byte[] salt = Base64.getDecoder().decode(encryptedValue.getSalt());

            // 2. IV와 암호문 분리
            byte[] iv = new byte[GCM_IV_LENGTH];
            byte[] ciphertext = new byte[encryptedData.length - GCM_IV_LENGTH];

            System.arraycopy(encryptedData, 0, iv, 0, iv.length);
            System.arraycopy(encryptedData, iv.length, ciphertext, 0, ciphertext.length);

            // 3. 암호화 키 유도
            SecretKey key = deriveKey(salt);

            // 4. 복호화 수행
            Cipher cipher = Cipher.getInstance(TRANSFORMATION);
            GCMParameterSpec parameterSpec = new GCMParameterSpec(GCM_TAG_LENGTH * 8, iv);
            cipher.init(Cipher.DECRYPT_MODE, key, parameterSpec);

            byte[] plaintext = cipher.doFinal(ciphertext);

            log.debug("Successfully decrypted data");

            return new String(plaintext, StandardCharsets.UTF_8);

        } catch (Exception e) {
            log.error("Failed to decrypt data", e);
            throw new EncryptionException("Decryption failed", e);
        }
    }

    /**
     * 새로운 암호화 키 생성 (테스트용)
     */
    public String generateNewMasterKey() {
        try {
            KeyGenerator keyGenerator = KeyGenerator.getInstance(ALGORITHM);
            keyGenerator.init(KEY_LENGTH);
            SecretKey key = keyGenerator.generateKey();
            
            String encodedKey = Base64.getEncoder().encodeToString(key.getEncoded());
            log.info("Generated new master key (length: {} chars)", encodedKey.length());
            
            return encodedKey;
        } catch (NoSuchAlgorithmException e) {
            log.error("Failed to generate master key", e);
            throw new EncryptionException("Failed to generate master key", e);
        }
    }

    // Private helper methods

    private byte[] generateSalt() {
        byte[] salt = new byte[SALT_LENGTH];
        secureRandom.nextBytes(salt);
        return salt;
    }

    private byte[] generateIV() {
        byte[] iv = new byte[GCM_IV_LENGTH];
        secureRandom.nextBytes(iv);
        return iv;
    }

    private SecretKey deriveKey(byte[] salt) {
        try {
            // 간단한 키 유도 (실제로는 PBKDF2, scrypt, Argon2 등 사용 권장)
            byte[] masterKeyBytes = masterKey.getBytes(StandardCharsets.UTF_8);
            byte[] keyMaterial = new byte[32]; // 256 bits

            // Salt와 마스터키 결합하여 키 생성
            for (int i = 0; i < keyMaterial.length; i++) {
                keyMaterial[i] = (byte) (
                    salt[i % salt.length] ^ 
                    masterKeyBytes[i % masterKeyBytes.length]
                );
            }

            return new SecretKeySpec(keyMaterial, ALGORITHM);
        } catch (Exception e) {
            log.error("Failed to derive encryption key", e);
            throw new EncryptionException("Key derivation failed", e);
        }
    }

    private String extractJsonValue(String json, String key) {
        // 간단한 JSON 값 추출 (실제로는 Jackson ObjectMapper 사용 권장)
        String searchKey = "\"" + key + "\":\"";
        int startIndex = json.indexOf(searchKey);
        if (startIndex == -1) {
            throw new IllegalArgumentException("Key not found in JSON: " + key);
        }

        startIndex += searchKey.length();
        int endIndex = json.indexOf("\"", startIndex);
        if (endIndex == -1) {
            throw new IllegalArgumentException("Invalid JSON format");
        }

        return json.substring(startIndex, endIndex);
    }

    private String maskString(String input, int visibleChars) {
        if (input == null || input.length() <= visibleChars) {
            return "***";
        }
        return input.substring(0, visibleChars) + "***";
    }

    /**
     * 암호화 관련 예외
     */
    public static class EncryptionException extends RuntimeException {
        public EncryptionException(String message) {
            super(message);
        }

        public EncryptionException(String message, Throwable cause) {
            super(message, cause);
        }
    }
}