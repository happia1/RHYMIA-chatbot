# prompts.py
# RHYMIA 챗봇의 시스템 프롬프트와 대화용 프롬프트 템플릿을 정의합니다.
# LangChain의 SystemMessagePromptTemplate을 사용해 확장·수정이 쉽게 구성했습니다.

from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)

# ---------------------------------------------------------------------------
# RHYMIA 정체성: 시스템 프롬프트 내용
# 서비스 성격에 맞게 문구를 수정해 사용할 수 있습니다.
# ---------------------------------------------------------------------------
RHYMIA_SYSTEM_PROMPT = """당신은 RHYMIA(리미아)입니다.

- RHYMIA는 사용자에게 친근하고 도움이 되는 AI 어시스턴트입니다.
- 말투는 따뜻하고 정중하며, 필요한 정보를 명확히 전달합니다.
- 질문에 성실히 답하고, 모르는 것은 솔직히 말하며 대안을 제시합니다.
- 답변은 간결하되 핵심을 놓치지 않도록 합니다.
- 사용자의 맥락과 감정을 고려한 응답을 합니다.

이 지침에 따라 사용자와 대화하세요."""


def build_chat_prompt() -> ChatPromptTemplate:
    """
    시스템 메시지(리미아 정체성) + 사용자 입력을 담는 채팅 프롬프트를 만듭니다.
    SystemMessagePromptTemplate으로 RHYMIA 정체성을 고정하고,
    HumanMessagePromptTemplate으로 매 턴 사용자 입력을 받습니다.
    나중에 변수(예: 사용자 이름, 서비스명)를 넣고 싶으면
    RHYMIA_SYSTEM_PROMPT를 f-string 또는 PromptTemplate으로 바꾸면 됩니다.
    """
    system_prompt = SystemMessagePromptTemplate.from_template(RHYMIA_SYSTEM_PROMPT)
    human_prompt = HumanMessagePromptTemplate.from_template("{user_input}")

    return ChatPromptTemplate.from_messages([
        system_prompt,
        human_prompt,
    ])
