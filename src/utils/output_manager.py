#!/usr/bin/env python3
"""
출력 파일 경로 관리 유틸리티
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional


def get_wip_output_path(vault_path: str, filename: str, create_dir: bool = True) -> str:
    """
    WIP 폴더에 출력 파일 경로 생성
    
    Args:
        vault_path: vault 경로
        filename: 파일명
        create_dir: WIP 디렉토리 자동 생성 여부
    
    Returns:
        WIP 폴더의 출력 파일 절대 경로
    """
    vault_dir = Path(vault_path)
    wip_dir = vault_dir / "WIP"
    
    # WIP 디렉토리 생성
    if create_dir and not wip_dir.exists():
        wip_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 WIP 디렉토리 생성: {wip_dir}")
    
    # 파일 경로 생성
    output_path = wip_dir / filename
    
    # 파일이 이미 존재하면 타임스탬프 추가
    if output_path.exists():
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{name}_{timestamp}.{ext}" if ext else f"{name}_{timestamp}"
        output_path = wip_dir / new_filename
        print(f"📝 파일명 중복 방지: {new_filename}")
    
    return str(output_path)


def resolve_output_path(vault_path: str, output_arg: Optional[str], command_name: str, topic: Optional[str] = None) -> Optional[str]:
    """
    --output 플래그가 제공되었을 때만 출력 경로 결정
    
    Args:
        vault_path: vault 경로
        output_arg: CLI --output 인자값 (None이면 파일 저장 안함)
        command_name: 명령어 이름 (기본 파일명 생성용)
        topic: 주제 (파일명에 포함할 경우)
    
    Returns:
        최종 출력 파일 경로 (output_arg가 None이면 None 반환)
    """
    # --output 플래그가 제공되지 않은 경우 파일 저장하지 않음
    if output_arg is None:
        return None
    
    # --output 플래그만 제공된 경우 (값 없음) - 기본 파일명 생성
    if output_arg == "":
        default_filename = generate_default_filename(command_name, topic)
        return get_wip_output_path(vault_path, default_filename)
    
    # --output "filename.md" 형태로 파일명이 제공된 경우
    if output_arg:
        # 절대 경로인 경우 그대로 사용
        if os.path.isabs(output_arg):
            return output_arg
        
        # 상대 경로인 경우 WIP 디렉토리에서 해석
        return get_wip_output_path(vault_path, output_arg)
    
    return None


def generate_default_filename(command_name: str, topic: Optional[str] = None, extension: str = "md") -> str:
    """
    명령어별 기본 파일명 생성
    
    Args:
        command_name: 명령어 이름 
        topic: 주제 (있으면 파일명에 포함)
        extension: 파일 확장자
    
    Returns:
        타임스탬프가 포함된 기본 파일명
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if topic:
        safe_topic = topic.replace(' ', '-').replace('/', '-')
        return f"{command_name}-{safe_topic}_{timestamp}.{extension}"
    else:
        return f"{command_name}-result_{timestamp}.{extension}"


def generate_timestamped_filename(base_name: str, extension: str = "md") -> str:
    """
    타임스탬프가 포함된 파일명 생성
    
    Args:
        base_name: 기본 파일명
        extension: 확장자 (기본값: md)
    
    Returns:
        타임스탬프가 포함된 파일명
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"


def ensure_wip_directory(vault_path: str) -> Path:
    """
    WIP 디렉토리가 존재하는지 확인하고 없으면 생성
    
    Args:
        vault_path: vault 경로
    
    Returns:
        WIP 디렉토리 Path 객체
    """
    wip_dir = Path(vault_path) / "WIP"
    wip_dir.mkdir(parents=True, exist_ok=True)
    return wip_dir