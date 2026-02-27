# config.py
# 설정 파일: YAML 로드, LLM 파라미터, 환경 변수 관리
# 비개발자: 이 파일은 앱이 사용하는 "설정값"을 한곳에서 관리합니다.

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# .env 파일에서 API 키 등 비밀값 로드 (있는 경우)
load_dotenv()

# ============== 경로 설정 ==============
# 프로젝트 루트 기준으로 prompts.yaml 위치 고정
BASE_DIR = Path(__file__).resolve().parent
PROMPTS_PATH = BASE_DIR / "prompts.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    """
    YAML 파일을 읽어서 파이썬 딕셔너리로 반환합니다.
    비개발자: prompts.yaml 같은 설정 파일을 프로그램이 읽을 수 있게 변환하는 함수입니다.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_prompts() -> dict[str, Any]:
    """prompts.yaml 내용을 로드해 반환합니다."""
    return load_yaml(PROMPTS_PATH)


# ============== LLM 파라미터 ==============
# Google Gemini 사용 (무료 티어: gemini-1.5-flash)
LLM_CONFIG = {
    "model": "gemini-1.5-flash",
    "temperature": 0.75,
}

HISTORY_WINDOW = 10  


# API 키는 환경 변수에서 읽음 (보안)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

