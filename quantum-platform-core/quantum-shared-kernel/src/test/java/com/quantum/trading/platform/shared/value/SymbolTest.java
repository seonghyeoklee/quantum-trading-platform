package com.quantum.trading.platform.shared.value;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class SymbolTest {
    
    @Test
    void shouldCreateValidKoreanStockSymbol() {
        Symbol symbol = Symbol.of("005930");
        
        assertEquals("005930", symbol.getValue());
        assertFalse(symbol.isPreferredStock());
        assertEquals("005930", symbol.getBaseCode());
    }
    
    @Test
    void shouldCreateValidPreferredStock() {
        Symbol symbol = Symbol.of("A005930");
        
        assertEquals("A005930", symbol.getValue());
        assertTrue(symbol.isPreferredStock());
        assertEquals("005930", symbol.getBaseCode());
    }
    
    @Test
    void shouldThrowExceptionForInvalidSymbol() {
        assertThrows(IllegalArgumentException.class, () -> Symbol.of("12345"));  // 5자리
        assertThrows(IllegalArgumentException.class, () -> Symbol.of("1234567")); // 7자리이지만 A로 시작하지 않음
        assertThrows(IllegalArgumentException.class, () -> Symbol.of("abcdef"));  // 문자
        assertThrows(IllegalArgumentException.class, () -> Symbol.of(""));       // 빈 문자열
        assertThrows(IllegalArgumentException.class, () -> Symbol.of(null));     // null
    }
    
    @Test
    void shouldTrimWhitespace() {
        Symbol symbol = Symbol.of("  005930  ");
        
        assertEquals("005930", symbol.getValue());
    }
    
    @Test
    void shouldReturnStringRepresentation() {
        Symbol symbol = Symbol.of("005930");
        
        assertEquals("005930", symbol.toString());
    }
}