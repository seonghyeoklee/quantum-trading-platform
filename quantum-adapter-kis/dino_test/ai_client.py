#!/usr/bin/env python3
"""
통합 AI 클라이언트
Claude API를 우선적으로 사용하고, OpenAI API를 폴백으로 사용하는 AI 분석 클라이언트
"""

import logging
import os
import json
from typing import Optional, Dict, List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()

class AIClient:
    """통합 AI 클라이언트 - Claude API 우선, OpenAI 폴백"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 환경변수에서 API 키 및 설정 읽기
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.ai_provider = os.getenv("AI_PROVIDER", "claude").lower()
        self.ai_debug = os.getenv("AI_DEBUG", "false").lower() == "true"
        
        # API 클라이언트 초기화
        self.anthropic_client = None
        self.openai_client = None
        
        self._init_claude_client()
        self._init_openai_client()
        
        # 사용 가능한 클라이언트 로깅
        providers = []
        if self.anthropic_client:
            providers.append("Claude")
        if self.openai_client:
            providers.append("OpenAI")
        
        if providers:
            self.logger.info(f"✅ AI 클라이언트 초기화 완료: {', '.join(providers)}")
        else:
            self.logger.warning("⚠️ 사용 가능한 AI API가 없습니다")
    
    def _init_claude_client(self):
        """Claude API 클라이언트 초기화"""
        if not self.anthropic_key:
            self.logger.warning("Anthropic API 키가 없습니다")
            return
        
        try:
            import anthropic
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_key)
            self.logger.info("✅ Claude API 클라이언트 초기화 완료")
        except ImportError:
            self.logger.error("anthropic 패키지가 설치되지 않았습니다: pip install anthropic")
        except Exception as e:
            self.logger.error(f"Claude API 클라이언트 초기화 실패: {e}")
    
    def _init_openai_client(self):
        """OpenAI API 클라이언트 초기화"""
        if not self.openai_key:
            self.logger.warning("OpenAI API 키가 없습니다")
            return
        
        try:
            import openai
            openai.api_key = self.openai_key
            self.openai_client = openai
            self.logger.info("✅ OpenAI API 클라이언트 초기화 완료")
        except ImportError:
            self.logger.error("openai 패키지가 설치되지 않았습니다: pip install openai")
        except Exception as e:
            self.logger.error(f"OpenAI API 클라이언트 초기화 실패: {e}")
    
    def analyze_with_claude(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Claude API로 텍스트 분석"""
        if not self.anthropic_client:
            return None
        
        try:
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",  # 빠르고 경제적인 모델
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            result = response.content[0].text.strip()
            
            if self.ai_debug:
                self.logger.debug(f"Claude API 응답: {result[:200]}...")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Claude API 호출 실패: {e}")
            return None
    
    def analyze_with_openai(self, system_prompt: str, user_prompt: str, max_tokens: int = 800) -> Optional[str]:
        """OpenAI API로 텍스트 분석 (폴백)"""
        if not self.openai_client:
            return None
        
        try:
            response = self.openai_client.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            result = response.choices[0].message.content.strip()
            
            if self.ai_debug:
                self.logger.debug(f"OpenAI API 응답: {result[:200]}...")
            
            return result
            
        except Exception as e:
            self.logger.error(f"OpenAI API 호출 실패: {e}")
            return None
    
    def analyze_text(self, system_prompt: str, user_prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """
        통합 텍스트 분석 - Claude 우선, OpenAI 폴백
        
        Args:
            system_prompt: 시스템 프롬프트 (분석 지침)
            user_prompt: 사용자 프롬프트 (분석할 내용)
            max_tokens: 최대 토큰 수
            
        Returns:
            분석 결과 텍스트 또는 None
        """
        
        # 1차: Claude API 시도
        if self.ai_provider == "claude" or self.ai_provider == "anthropic":
            result = self.analyze_with_claude(system_prompt, user_prompt, max_tokens)
            if result:
                self.logger.info("✅ Claude API로 분석 완료")
                return result
            else:
                self.logger.warning("Claude API 실패, OpenAI로 폴백 시도")
        
        # 2차: OpenAI API 폴백
        result = self.analyze_with_openai(system_prompt, user_prompt, max_tokens)
        if result:
            self.logger.info("✅ OpenAI API로 분석 완료 (폴백)")
            return result
        
        # 모든 API 실패
        self.logger.error("❌ 모든 AI API 호출 실패")
        return None
    
    def parse_json_response(self, response_text: str) -> Optional[Dict]:
        """AI 응답에서 JSON 추출 및 파싱"""
        if not response_text:
            return None
        
        try:
            # 전체 텍스트를 JSON으로 파싱 시도
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # JSON 블록 찾기 시도
        import re
        
        # ```json ... ``` 패턴 찾기
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # { ... } 패턴 찾기
        brace_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(brace_pattern, response_text, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue
        
        self.logger.warning(f"JSON 파싱 실패: {response_text[:100]}...")
        return None
    
    def is_available(self) -> bool:
        """AI 클라이언트 사용 가능 여부"""
        return self.anthropic_client is not None or self.openai_client is not None
    
    def get_available_providers(self) -> List[str]:
        """사용 가능한 AI 제공자 목록"""
        providers = []
        if self.anthropic_client:
            providers.append("claude")
        if self.openai_client:
            providers.append("openai")
        return providers


# 전역 AI 클라이언트 인스턴스
_ai_client_instance = None

def get_ai_client() -> AIClient:
    """전역 AI 클라이언트 인스턴스 반환 (싱글톤)"""
    global _ai_client_instance
    
    if _ai_client_instance is None:
        _ai_client_instance = AIClient()
    
    return _ai_client_instance


if __name__ == "__main__":
    # 테스트 코드
    logging.basicConfig(level=logging.INFO)
    
    client = get_ai_client()
    
    print(f"사용 가능한 제공자: {client.get_available_providers()}")
    
    if client.is_available():
        # 간단한 테스트
        system_prompt = "당신은 한국어 텍스트 분석 전문가입니다."
        user_prompt = "다음 문장의 감정을 분석해주세요: '삼성전자가 신제품을 출시했습니다.'"
        
        result = client.analyze_text(system_prompt, user_prompt, max_tokens=200)
        print(f"분석 결과: {result}")
    else:
        print("❌ 사용 가능한 AI 클라이언트가 없습니다")