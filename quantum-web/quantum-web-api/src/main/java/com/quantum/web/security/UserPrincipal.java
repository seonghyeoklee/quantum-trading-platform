package com.quantum.web.security;

import lombok.Builder;
import lombok.Data;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.util.Collection;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * User Principal
 * 
 * Spring Security에서 사용하는 사용자 주체 정보
 * - JWT 토큰에서 추출한 사용자 정보를 담는 객체
 * - UserDetails 인터페이스 구현으로 Spring Security와 연동
 * - 권한 정보 및 계정 상태 관리
 */
@Data
@Builder
public class UserPrincipal implements UserDetails {

    private String id;
    private String username;
    private String email;
    private String name;
    private Collection<? extends GrantedAuthority> authorities;
    
    // 계정 상태 정보
    @Builder.Default
    private boolean accountNonExpired = true;
    
    @Builder.Default
    private boolean accountNonLocked = true;
    
    @Builder.Default
    private boolean credentialsNonExpired = true;
    
    @Builder.Default
    private boolean enabled = true;

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return authorities;
    }

    @Override
    public String getPassword() {
        // JWT 기반 인증에서는 비밀번호 불필요
        return null;
    }

    @Override
    public String getUsername() {
        return username;
    }

    @Override
    public boolean isAccountNonExpired() {
        return accountNonExpired;
    }

    @Override
    public boolean isAccountNonLocked() {
        return accountNonLocked;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return credentialsNonExpired;
    }

    @Override
    public boolean isEnabled() {
        return enabled;
    }

    /**
     * 사용자가 특정 권한을 가지고 있는지 확인
     */
    public boolean hasRole(String role) {
        return authorities.stream()
                .anyMatch(auth -> auth.getAuthority().equals("ROLE_" + role) || 
                                auth.getAuthority().equals(role));
    }

    /**
     * 사용자가 여러 권한 중 하나라도 가지고 있는지 확인
     */
    public boolean hasAnyRole(String... roles) {
        for (String role : roles) {
            if (hasRole(role)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 사용자의 모든 권한 문자열 반환
     */
    public Set<String> getRoleNames() {
        return authorities.stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toSet());
    }

    /**
     * 관리자 권한 여부 확인
     */
    public boolean isAdmin() {
        return hasRole("ADMIN");
    }

    /**
     * 매니저 권한 여부 확인
     */
    public boolean isManager() {
        return hasRole("MANAGER");
    }

    /**
     * 트레이더 권한 여부 확인
     */
    public boolean isTrader() {
        return hasRole("TRADER");
    }

    /**
     * 사용자 정보 요약 (로깅용)
     */
    public String toSummaryString() {
        return String.format("UserPrincipal{id='%s', username='%s', roles=%s, enabled=%s}", 
                           id, username, getRoleNames(), enabled);
    }
}