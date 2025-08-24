#!/usr/bin/env python3
"""
Claude Code Integration Module for Vault Intelligence System V2 - Phase 9

Claude Code의 Task 도구를 활용한 LLM 통합 모듈
"""

import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """LLM 요청 정보"""
    prompt: str
    subagent_type: str = "general-purpose"
    description: str = "문서 요약 생성"
    max_retries: int = 3
    timeout: int = 300


@dataclass
class LLMResponse:
    """LLM 응답 정보"""
    success: bool
    content: str
    processing_time: float
    retry_count: int
    error_message: Optional[str] = None


class ClaudeCodeIntegration:
    """Claude Code Task 도구 연동 클래스"""
    
    def __init__(self, config: dict):
        """
        ClaudeCodeIntegration 초기화
        
        Args:
            config: 설정 정보
        """
        self.config = config
        claude_config = config.get('document_summarization', {}).get('claude_code_integration', {})
        
        self.default_subagent_type = claude_config.get('subagent_type', 'general-purpose')
        self.default_max_retries = claude_config.get('max_retries', 3)
        self.default_timeout = claude_config.get('timeout', 300)
        
        # Task 도구는 실행시 동적으로 사용 (현재는 Mock)
        self.task_tool = None
        
        logger.info("Claude Code 통합 모듈 초기화 완료")
    
    def call_llm(self, request: LLMRequest) -> LLMResponse:
        """
        Claude Code LLM 호출
        
        Args:
            request: LLM 요청 정보
            
        Returns:
            LLMResponse: LLM 응답 정보
        """
        start_time = time.time()
        retry_count = 0
        
        logger.info(f"Claude Code LLM 호출: {request.description}")
        
        for attempt in range(request.max_retries):
            try:
                retry_count = attempt
                
                # 실제 Claude Code Task 도구 호출
                result = self._call_task_tool(request)
                
                processing_time = time.time() - start_time
                
                # 성공 응답
                response = LLMResponse(
                    success=True,
                    content=result,
                    processing_time=processing_time,
                    retry_count=retry_count
                )
                
                logger.info(f"LLM 호출 성공 (시도: {retry_count + 1}, 시간: {processing_time:.2f}초)")
                return response
                
            except Exception as e:
                logger.warning(f"LLM 호출 실패 (시도 {attempt + 1}/{request.max_retries}): {e}")
                
                if attempt == request.max_retries - 1:
                    # 최종 실패
                    processing_time = time.time() - start_time
                    return LLMResponse(
                        success=False,
                        content="",
                        processing_time=processing_time,
                        retry_count=retry_count,
                        error_message=str(e)
                    )
                
                # 재시도 전 대기
                time.sleep(2 ** attempt)  # 지수 백오프
        
        # 이 지점에 도달하면 안됨
        return LLMResponse(
            success=False,
            content="",
            processing_time=time.time() - start_time,
            retry_count=retry_count,
            error_message="최대 재시도 횟수 초과"
        )
    
    def _call_task_tool(self, request: LLMRequest) -> str:
        """
        실제 Task 도구 호출
        
        현재는 Mock 구현이지만, 실제 구현에서는 다음과 같이 사용:
        
        task_result = Task(
            subagent_type=request.subagent_type,
            description=request.description,
            prompt=request.prompt
        )
        
        return task_result
        """
        logger.info(f"Task 도구 호출 중... (Mock 구현)")
        
        # Mock 응답 생성 (실제로는 Task 도구가 반환하는 값)
        mock_response = self._generate_mock_response(request.prompt)
        
        # 실제 처리 시간 시뮬레이션
        time.sleep(1)  # 1초 대기
        
        return mock_response
    
    def _generate_mock_response(self, prompt: str) -> str:
        """Mock 응답 생성 (개발/테스트용)"""
        
        # 프롬프트 분석하여 적절한 Mock 응답 생성
        if "요약" in prompt:
            return self._generate_summary_mock()
        elif "인사이트" in prompt:
            return self._generate_insights_mock()
        elif "개념" in prompt:
            return self._generate_concepts_mock()
        else:
            return "Claude Code LLM에서 처리된 응답입니다."
    
    def _generate_summary_mock(self) -> str:
        """요약 Mock 응답 생성"""
        return """## 핵심 요약
이 문서 그룹은 소프트웨어 개발의 핵심 개념들을 다루고 있습니다. 테스트 주도 개발, 리팩토링, 클린코드 등의 주제를 통해 고품질 소프트웨어 개발 방법론을 제시합니다.

## 주요 인사이트
- 테스트 주도 개발은 설계 도구로서의 가치가 높습니다
- 지속적인 리팩토링이 코드 품질 유지의 핵심입니다
- 읽기 쉬운 코드가 유지보수 비용을 크게 절약합니다

## 핵심 개념
- TDD (Test-Driven Development)
- 리팩토링 (Refactoring)
- 클린코드 (Clean Code)

## 실용적 팁
- 작은 단위로 테스트를 작성하세요
- 코드 리뷰를 통해 품질을 지속적으로 개선하세요"""
    
    def _generate_insights_mock(self) -> str:
        """인사이트 Mock 응답 생성"""
        return """주요 인사이트:
1. 개발 방법론의 일관된 적용이 중요합니다
2. 팀 전체의 합의가 성공의 열쇠입니다
3. 점진적 개선이 급격한 변화보다 효과적입니다"""
    
    def _generate_concepts_mock(self) -> str:
        """개념 Mock 응답 생성"""
        return """핵심 개념:
- 소프트웨어 품질
- 개발 생산성
- 유지보수성"""
    
    def summarize_documents(self, 
                          content: str, 
                          cluster_info: Dict,
                          style: str = "detailed") -> Dict[str, Any]:
        """
        문서 그룹 요약 생성
        
        Args:
            content: 요약할 문서 내용
            cluster_info: 클러스터 정보
            style: 요약 스타일
            
        Returns:
            Dict: 파싱된 요약 결과
        """
        # 요약 프롬프트 생성
        prompt = self._create_summarization_prompt(content, cluster_info, style)
        
        # LLM 요청 생성
        request = LLMRequest(
            prompt=prompt,
            subagent_type=self.default_subagent_type,
            description=f"{cluster_info.get('label', 'Unknown')} 클러스터 요약",
            max_retries=self.default_max_retries,
            timeout=self.default_timeout
        )
        
        # LLM 호출
        response = self.call_llm(request)
        
        if not response.success:
            raise Exception(f"요약 생성 실패: {response.error_message}")
        
        # 응답 파싱
        parsed_result = self._parse_summary_response(response.content)
        return parsed_result
    
    def _create_summarization_prompt(self, content: str, cluster_info: Dict, style: str) -> str:
        """요약을 위한 프롬프트 생성"""
        
        style_instructions = {
            'brief': '간결하고 핵심적인 요약을 3문장 이내로 작성해주세요.',
            'detailed': '상세하고 포괄적인 요약을 5-10문장으로 작성해주세요.',
            'technical': '기술적 세부사항에 중점을 둔 요약을 8문장 이내로 작성해주세요.',
            'conceptual': '개념과 원칙 중심의 요약을 6문장 이내로 작성해주세요.'
        }
        
        cluster_label = cluster_info.get('label', 'Unknown')
        keywords = ', '.join(cluster_info.get('keywords', []))
        document_count = cluster_info.get('size', 0)
        
        prompt = f"""
다음은 "{cluster_label}"이라는 주제로 분류된 {document_count}개 문서의 내용입니다.
키워드: {keywords}

{style_instructions.get(style, style_instructions['detailed'])}

문서 내용:
{content}

다음 형식으로 요약해주세요:

## 핵심 요약
[{style} 스타일의 요약]

## 주요 인사이트
- [인사이트 1]
- [인사이트 2] 
- [인사이트 3]

## 핵심 개념
- [개념 1]
- [개념 2]

## 실용적 팁
- [팁 1]
- [팁 2]

한국어로 답변해주세요.
        """.strip()
        
        return prompt
    
    def _parse_summary_response(self, response_content: str) -> Dict[str, Any]:
        """요약 응답 파싱"""
        
        result = {
            'summary': '',
            'insights': [],
            'concepts': [],
            'tips': []
        }
        
        lines = response_content.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('## 핵심 요약'):
                current_section = 'summary'
            elif line.startswith('## 주요 인사이트'):
                current_section = 'insights'
            elif line.startswith('## 핵심 개념'):
                current_section = 'concepts'
            elif line.startswith('## 실용적 팁'):
                current_section = 'tips'
            elif line and not line.startswith('##'):
                if current_section == 'summary':
                    result['summary'] += line + ' '
                elif current_section in ['insights', 'concepts', 'tips'] and line.startswith('- '):
                    item = line[2:].strip()
                    if item:
                        result[current_section].append(item)
        
        # 요약 텍스트 정리
        result['summary'] = result['summary'].strip()
        
        return result


def test_claude_code_integration():
    """Claude Code 통합 모듈 테스트"""
    print("🧪 Claude Code 통합 모듈 테스트 시작...")
    
    try:
        # 설정
        config = {
            'document_summarization': {
                'claude_code_integration': {
                    'subagent_type': 'general-purpose',
                    'max_retries': 2,
                    'timeout': 30
                }
            }
        }
        
        # 통합 모듈 생성
        integration = ClaudeCodeIntegration(config)
        
        # 기본 LLM 호출 테스트
        request = LLMRequest(
            prompt="테스트 프롬프트입니다",
            description="테스트 호출"
        )
        
        response = integration.call_llm(request)
        
        # 결과 검증
        assert response is not None, "응답이 없음"
        assert response.success, f"LLM 호출 실패: {response.error_message}"
        assert len(response.content) > 0, "응답 내용이 비어있음"
        assert response.processing_time > 0, "처리 시간 오류"
        
        print(f"✅ 기본 LLM 호출 성공")
        print(f"   응답 길이: {len(response.content)}자")
        print(f"   처리 시간: {response.processing_time:.2f}초")
        
        # 문서 요약 테스트
        cluster_info = {
            'label': 'TDD 기본 개념',
            'keywords': ['tdd', 'testing', 'refactoring'],
            'size': 5
        }
        
        content = "테스트 주도 개발에 대한 문서 내용입니다..."
        
        summary_result = integration.summarize_documents(content, cluster_info, "detailed")
        
        # 요약 결과 검증
        assert 'summary' in summary_result, "요약이 없음"
        assert 'insights' in summary_result, "인사이트가 없음"
        assert len(summary_result['summary']) > 0, "요약 내용이 비어있음"
        
        print(f"✅ 문서 요약 성공")
        print(f"   요약 길이: {len(summary_result['summary'])}자")
        print(f"   인사이트 수: {len(summary_result['insights'])}개")
        print(f"   개념 수: {len(summary_result['concepts'])}개")
        print(f"   팁 수: {len(summary_result['tips'])}개")
        
        return True
        
    except Exception as e:
        print(f"❌ Claude Code 통합 모듈 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    test_claude_code_integration()