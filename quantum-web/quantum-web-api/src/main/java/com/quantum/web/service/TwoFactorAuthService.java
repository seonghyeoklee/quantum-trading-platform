package com.quantum.web.service;

import com.eatthepath.otp.TimeBasedOneTimePasswordGenerator;
import com.google.zxing.BarcodeFormat;
import com.google.zxing.client.j2se.MatrixToImageWriter;
import com.google.zxing.common.BitMatrix;
import com.google.zxing.qrcode.QRCodeWriter;
import com.quantum.trading.platform.shared.value.UserId;
import org.apache.commons.codec.binary.Base32;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import javax.crypto.KeyGenerator;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;
import java.io.ByteArrayOutputStream;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;
import java.security.InvalidKeyException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.time.Duration;
import java.time.Instant;
import java.util.*;

/**
 * TOTP (Time-based One-Time Password) 2FA 서비스
 * RFC 6238 표준을 구현하여 Google Authenticator와 호환
 */
@Service
public class TwoFactorAuthService {
    
    private static final Logger logger = LoggerFactory.getLogger(TwoFactorAuthService.class);
    
    private static final String HMAC_ALGORITHM = "HmacSHA1";
    private static final int SECRET_KEY_LENGTH = 20; // 160 bits
    private static final int TIME_STEP_SECONDS = 30;
    private static final int CODE_DIGITS = 6;
    private static final int WINDOW_SIZE = 1; // 허용할 시간 윈도우 (±30초)
    
    @Value("${app.name:Quantum Trading}")
    private String applicationName;
    
    @Value("${app.domain:quantum-trading.com}")
    private String applicationDomain;
    
    private final TimeBasedOneTimePasswordGenerator totpGenerator;
    private final Base32 base32 = new Base32();
    private final SecureRandom secureRandom = new SecureRandom();
    
    public TwoFactorAuthService() {
        this.totpGenerator = new TimeBasedOneTimePasswordGenerator(
            Duration.ofSeconds(TIME_STEP_SECONDS),
            CODE_DIGITS
        );
    }
    
    /**
     * 새로운 TOTP 시크릿 키 생성
     */
    public String generateSecretKey() {
        byte[] secretKey = new byte[SECRET_KEY_LENGTH];
        secureRandom.nextBytes(secretKey);
        return base32.encodeAsString(secretKey);
    }
    
    /**
     * QR 코드용 URL 생성
     * otpauth://totp/{issuer}:{username}?secret={secret}&issuer={issuer}
     */
    public String generateQrCodeUrl(String username, String secretKey) {
        try {
            String encodedUsername = URLEncoder.encode(username, "UTF-8");
            String encodedIssuer = URLEncoder.encode(applicationName, "UTF-8");
            
            return String.format(
                "otpauth://totp/%s:%s?secret=%s&issuer=%s&algorithm=SHA1&digits=%d&period=%d",
                encodedIssuer,
                encodedUsername,
                secretKey,
                encodedIssuer,
                CODE_DIGITS,
                TIME_STEP_SECONDS
            );
        } catch (UnsupportedEncodingException e) {
            logger.error("Failed to encode QR code URL parameters", e);
            throw new RuntimeException("Failed to generate QR code URL", e);
        }
    }
    
    /**
     * QR 코드 이미지 생성 (Base64)
     */
    public String generateQrCodeImage(String qrCodeUrl, int width, int height) {
        try {
            QRCodeWriter qrCodeWriter = new QRCodeWriter();
            BitMatrix bitMatrix = qrCodeWriter.encode(qrCodeUrl, BarcodeFormat.QR_CODE, width, height);
            
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            MatrixToImageWriter.writeToStream(bitMatrix, "PNG", outputStream);
            
            byte[] imageBytes = outputStream.toByteArray();
            return Base64.getEncoder().encodeToString(imageBytes);
        } catch (Exception e) {
            logger.error("Failed to generate QR code image", e);
            throw new RuntimeException("Failed to generate QR code image", e);
        }
    }
    
    /**
     * 현재 시간 기준 TOTP 코드 생성
     */
    public String generateCurrentTotp(String secretKey) {
        try {
            byte[] decodedKey = base32.decode(secretKey);
            SecretKeySpec keySpec = new SecretKeySpec(decodedKey, HMAC_ALGORITHM);
            
            Instant now = Instant.now();
            return String.format("%06d", totpGenerator.generateOneTimePassword(keySpec, now));
        } catch (Exception e) {
            logger.error("Failed to generate TOTP code", e);
            throw new RuntimeException("Failed to generate TOTP code", e);
        }
    }
    
    /**
     * TOTP 코드 검증 (시간 윈도우 고려)
     */
    public boolean verifyTotp(String secretKey, String inputCode) {
        if (secretKey == null || inputCode == null || inputCode.length() != CODE_DIGITS) {
            return false;
        }
        
        try {
            byte[] decodedKey = base32.decode(secretKey);
            SecretKeySpec keySpec = new SecretKeySpec(decodedKey, HMAC_ALGORITHM);
            
            Instant now = Instant.now();
            
            // 현재 시간 윈도우와 앞뒤 윈도우에서 검증
            for (int i = -WINDOW_SIZE; i <= WINDOW_SIZE; i++) {
                Instant testTime = now.plusSeconds(i * TIME_STEP_SECONDS);
                String expectedCode = String.format("%06d", 
                    totpGenerator.generateOneTimePassword(keySpec, testTime));
                
                if (inputCode.equals(expectedCode)) {
                    logger.debug("TOTP verification successful for time window offset: {}", i);
                    return true;
                }
            }
            
            logger.debug("TOTP verification failed for input code: {}", inputCode);
            return false;
        } catch (Exception e) {
            logger.error("Error during TOTP verification", e);
            return false;
        }
    }
    
    /**
     * 백업 코드 생성 (8자리 랜덤 문자열 × 10개)
     */
    public List<String> generateBackupCodes() {
        List<String> backupCodes = new ArrayList<>();
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        
        for (int i = 0; i < 10; i++) {
            StringBuilder code = new StringBuilder();
            for (int j = 0; j < 8; j++) {
                code.append(chars.charAt(secureRandom.nextInt(chars.length())));
            }
            backupCodes.add(code.toString());
        }
        
        return backupCodes;
    }
    
    /**
     * 백업 코드 해시 생성 (저장용)
     */
    public String hashBackupCode(String backupCode) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            SecretKeySpec secretKeySpec = new SecretKeySpec(
                applicationDomain.getBytes(), "HmacSHA256"
            );
            mac.init(secretKeySpec);
            
            byte[] hash = mac.doFinal(backupCode.getBytes());
            return Base64.getEncoder().encodeToString(hash);
        } catch (NoSuchAlgorithmException | InvalidKeyException e) {
            logger.error("Failed to hash backup code", e);
            throw new RuntimeException("Failed to hash backup code", e);
        }
    }
    
    /**
     * 백업 코드 검증
     */
    public boolean verifyBackupCode(String inputCode, List<String> hashedBackupCodes) {
        if (inputCode == null || hashedBackupCodes == null) {
            return false;
        }
        
        String hashedInput = hashBackupCode(inputCode.toUpperCase().trim());
        return hashedBackupCodes.contains(hashedInput);
    }
    
    /**
     * 2FA 설정 데이터 생성
     */
    public TwoFactorSetupData generateSetupData(String username) {
        String secretKey = generateSecretKey();
        String qrCodeUrl = generateQrCodeUrl(username, secretKey);
        String qrCodeImage = generateQrCodeImage(qrCodeUrl, 200, 200);
        List<String> backupCodes = generateBackupCodes();
        
        return new TwoFactorSetupData(
            secretKey,
            qrCodeUrl,
            qrCodeImage,
            backupCodes
        );
    }
    
    /**
     * 2FA 설정 데이터 DTO
     */
    public static class TwoFactorSetupData {
        private final String secretKey;
        private final String qrCodeUrl;
        private final String qrCodeImage;
        private final List<String> backupCodes;
        
        public TwoFactorSetupData(String secretKey, String qrCodeUrl, 
                                 String qrCodeImage, List<String> backupCodes) {
            this.secretKey = secretKey;
            this.qrCodeUrl = qrCodeUrl;
            this.qrCodeImage = qrCodeImage;
            this.backupCodes = backupCodes;
        }
        
        public String getSecretKey() { return secretKey; }
        public String getQrCodeUrl() { return qrCodeUrl; }
        public String getQrCodeImage() { return qrCodeImage; }
        public List<String> getBackupCodes() { return backupCodes; }
    }
}