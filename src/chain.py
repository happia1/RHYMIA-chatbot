# chain.py
# LangChain의 ChatOpenAI와 프롬프트를 연결한 '체인'을 정의합니다.
# 단순 API 호출이 아니라 체인 구조로 두어, 나중에 메모리·도구·라우팅 등을 붙이기 쉽게 합니다.

import os
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

from .prompts import build_chat_prompt


def get_llm(model_name: str = "gpt-4o-mini", **kwargs):
    """
    ChatOpenAI 인스턴스를 생성합니다.
    .env의 OPENAI_API_KEY를 사용하며, 모델명·온도 등은 인자로 조정할 수 있습니다.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 넣어 주세요."
        )
    return ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        **kwargs,
    )


def build_chat_chain(model_name: str = "gpt-4o-mini", **llm_kwargs):
    """
    [프롬프트] -> [LLM] -> [문자열 출력] 파이프라인(체인)을 만듭니다.
    입력은 반드시 {"user_input": "사용자가 입력한 글"} 형태의 딕셔너리입니다.
    나중에 메모리·툴을 붙일 때는 여기서 체인을 확장하면 됩니다.
    """
    prompt = build_chat_prompt()
    llm = get_llm(model_name=model_name, **llm_kwargs)
    # 출력은 그냥 문자열로 쓰기 위해 StrOutputParser 사용
    output_parser = StrOutputParser()

    # LCEL 파이프라인: 입력(dict) -> 프롬프트 포맷 -> LLM -> 문자열 파싱
    # 나중에 메모리·도구를 붙이려면 이 파이프라인 앞뒤에 runnable을 추가하면 됩니다.
    chain = prompt | llm | output_parser
    return chain


def chat(chain, user_input: str) -> str:
    """
    이미 만든 체인에 사용자 입력을 넣고, RHYMIA의 답변 문자열을 반환합니다.
    """
    return chain.invoke({"user_input": user_input})
