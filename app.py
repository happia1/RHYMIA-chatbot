# app.py
import streamlit as st
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from chatbot import RYMIChatbot

st.set_page_config(
    page_title="RYMI 재무 코치",
    page_icon="💬",
    layout="centered",
)

# ============== 챗봇 인스턴스 + 채팅 기록 저장 ==============
# 세션에 저장해야 대화 히스토리가 유지돼요
if "chatbot" not in st.session_state:
    st.session_state.chatbot = RYMIChatbot()
    st.session_state.messages = []
    # 웰컴 메시지 추가
    welcome = st.session_state.chatbot.get_welcome_message()
    st.session_state.messages.append({"role": "assistant", "content": welcome})

# ============== 화면 제목 ==============
st.title("💬 RYMI")
st.caption("결혼 7년 이내 신혼부부를 위한 재무 코치")

# ============== 이전 대화 내역 표시 ==============
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ============== 사용자 입력 받기 ==============
if user_input := st.chat_input("재무 관련 질문을 입력해 보세요."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("RYMI가 생각하는 중이에요... 💭"):
            try:
                reply = st.session_state.chatbot.get_reply(user_input)
            except ChatGoogleGenerativeAIError as e:
                if "API key" in str(e).lower() or "expired" in str(e).lower():
                    reply = (
                        "⚠️ **Google API 키가 만료되었거나 유효하지 않아요.**\n\n"
                        "1. [Google AI Studio](https://aistudio.google.com/apikey)에서 새 API 키를 발급받으세요.\n"
                        "2. `.env` 파일의 `GOOGLE_API_KEY` 값을 새 키로 바꾼 뒤 앱을 다시 실행해 주세요."
                    )
                else:
                    reply = f"오류가 발생했어요: {e}"
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

# ============== 대화 초기화 버튼 ==============
if st.button("🔄 대화 초기화"):
    st.session_state.chatbot.reset()
    welcome = st.session_state.chatbot.get_welcome_message()
    st.session_state.messages = [{"role": "assistant", "content": welcome}]
    st.rerun()

st.divider()
st.caption("RYMI는 일반적인 재무 조언을 제공합니다. 구체적인 금융·법률·세무 결정은 전문가와 상담하세요.")