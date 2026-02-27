# run_chat.py
# RHYMIA 챗봇을 콘솔에서 실행하는 진입점 스크립트입니다.
# .env 파일을 로드한 뒤 LangChain 체인으로 사용자 입력에 답합니다.

import os
from dotenv import load_dotenv

from src.chain import build_chat_chain, chat


def main():
    # 프로젝트 루트의 .env에서 OPENAI_API_KEY 등을 로드
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("오류: .env 파일에 OPENAI_API_KEY가 없습니다. 설정 후 다시 실행해 주세요.")
        return

    # 4o-mini 모델로 체인 생성 (확장 가능한 구조)
    chain = build_chat_chain(model_name="gpt-4o-mini")

    print("RHYMIA(리미아) 챗봇이 준비되었습니다. 종료하려면 'quit' 또는 'exit'를 입력하세요.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n대화를 종료합니다.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "종료"):
            print("RHYMIA: 다음에 또 만나요!")
            break

        try:
            response = chat(chain, user_input)
            print(f"RHYMIA: {response}\n")
        except Exception as e:
            print(f"오류가 발생했습니다: {e}\n")


if __name__ == "__main__":
    main()
