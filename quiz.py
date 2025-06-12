# Terminal에 google-generativeai 설치
genai.configure(api_key="API_키")

model = genai.GenerativeModel("gemini-1.5-flash")


import google.generativeai as genai
import re

# 1. Gemini에게 퀴즈 요청하기
def make_quiz_with_gemini(text):
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        f"다음 뉴스 내용을 바탕으로 객관식 퀴즈 3문제를 만들어줘. "
        f"각 문제는 4개의 선택지와 정답 번호를 포함해야 해. "
        f"형식은 다음과 같아야 해:\n"
        f"문제 1: (내용)\n1. 보기1\n2. 보기2\n3. 보기3\n4. 보기4\n정답: (번호)\n\n뉴스:\n{text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

# 2. 퀴즈 텍스트 파싱하기
def parse_quiz_text(text):
    quiz_data = []
    pattern = r"문제\s*\d+[:：]\s*(.*?)\n1[.] (.*?)\n2[.] (.*?)\n3[.] (.*?)\n4[.] (.*?)\n정답[:：]\s*(\d)"
    matches = re.findall(pattern, text, re.DOTALL)

    for match in matches:
        question, opt1, opt2, opt3, opt4, answer = match
        quiz_data.append({
            "question": question.strip(),
            "options": [opt1.strip(), opt2.strip(), opt3.strip(), opt4.strip()],
            "answer": int(answer) - 1  # 0부터 시작하게 바꾸기
        })
    return quiz_data

# 3. 퀴즈 진행 함수
def run_quiz(quiz_list):
    print("📰 뉴스 기반 객관식 퀴즈를 시작합니다. 총 3문제입니다.\n")

    for i, quiz in enumerate(quiz_list):
        print(f"문제 {i + 1}: {quiz['question']}")
        for idx, option in enumerate(quiz["options"]):
            print(f"  {idx}. {option}")

        # 사용자 입력 받기
        while True:
            try:
                user_input = int(input("👉 정답 번호 입력 (0~3): "))
                if 0 <= user_input < 4:
                    break
                else:
                    print("보기 번호 중에서 골라주세요. (0~3)!")
            except ValueError:
                print("숫자만 입력해 주세요.")

        # 정답 체크
        if user_input == quiz["answer"]:
            print("✅ 정답입니다!\n")
        else:
            correct_option = quiz["options"][quiz["answer"]]
            print(f"❌ 정답은 [{quiz['answer']}. {correct_option}]입니다.\n")

    print("퀴즈가 끝났습니다.")

# -------------------------------
# 전체 실행 흐름
if __name__ == "__main__":
    # 예시 뉴스 텍스트 (테스트용)
    news_text = """
    한국은행은 오늘 기준금리를 0.25% 인상하며, 최근 급등하는 물가 상승을 억제하기 위한 조치를 발표했다.
    이는 지난 6개월간 처음으로 이루어진 금리 인상이며, 소비자 대출 이자에 직접적인 영향을 미칠 것으로 보인다.
    """

    quiz_text = make_quiz_with_gemini(news_text)
    print("🔍 생성된 퀴즈 텍스트:\n")
    print(quiz_text)  # 확인용 (실제로는 숨겨도 됨)

    quiz_data = parse_quiz_text(quiz_text)
    run_quiz(quiz_data)
