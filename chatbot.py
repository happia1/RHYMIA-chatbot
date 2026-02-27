# chatbot.py
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from config import LLM_CONFIG, GOOGLE_API_KEY, get_prompts, HISTORY_WINDOW


class RYMIChatbot:
    def __init__(self):
        prompts_config = get_prompts()
        system_message = prompts_config.get("system", "").strip()

        # 대화 히스토리 포함한 프롬프트 템플릿
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="history"),  # ← 히스토리 추가
            ("human", "{user_message}"),
        ])

        self.llm = ChatGoogleGenerativeAI(
            model=LLM_CONFIG["model"],
            temperature=LLM_CONFIG["temperature"],
            google_api_key=GOOGLE_API_KEY,
        )

        self.chain = self.prompt | self.llm | StrOutputParser()
        self.history = []  # 대화 기록 저장

    def get_reply(self, user_message: str) -> str:
        # 최근 N개만 유지 (토큰 절약)
        recent_history = self.history[-HISTORY_WINDOW:]

        response = self.chain.invoke({
            "history": recent_history,
            "user_message": user_message,
        })

        # 히스토리 업데이트
        self.history.append(HumanMessage(content=user_message))
        self.history.append(AIMessage(content=response))

        return response

    def reset(self):
        self.history = []

    def get_welcome_message(self) -> str:
        return (
            "안녕하세요! 저는 RYMI예요. 💛\n\n"
            "결혼 7년 이내 부부의 재무 고민을 함께 풀어나가는 RHYMIA의 AI 재무 코치예요.\n"
            "신혼 초기 예산 설계부터 청약 준비, 육아비·교육비 설계까지\n"
            "편하게 털어놓아 주세요. 🌱\n\n"
            "결혼 몇 년차이신가요? 시기에 맞는 이야기를 나눠볼게요!"
        )