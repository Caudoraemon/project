import urllib.request
import urllib.parse
import json
import google.generativeai as genai
from pathlib import Path

# 네이버 API 정보 입력
client_id = "BDqJGBPjsHXqekmaVY4e"
client_secret = "cS1s_5MfZC"

# Gemini API 키 입력
GEMINI_API_KEY = "AIzaSyD5KJKDx_0L8rx80k4sULj4TvB6Lg6ZO5Y"

# 뉴스 검색 함수
def get_news(query):
    # 입력 키워드를 URL 인코딩
    encText = urllib.parse.quote(query)
    # 뉴스 검색 URL 구성
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display=1&sort=sim"
    # 요청 객체 생성, 헤더 설정
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    # 인증 우회 SSL 설정
    import ssl
    ssl_context = ssl._create_unverified_context()
    # API 요청 및 응답 처리
    response = urllib.request.urlopen(request, context=ssl_context)
    rescode = response.getcode()
    if rescode == 200:
        response_body = response.read()
        news_json = json.loads(response_body)
        if news_json["items"]:
            return news_json["items"][0]
        else:
            print("검색 결과가 없습니다.")
            return None
    else:
        print("Error Code:" + str(rescode))
        return None

# 뉴스 설명 추출 함수
def get_article_text(news_item):
    return news_item['description']

# 수준별 요약 생성 함수
def summarize_by_level_with_gemini(level, text):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    level_map = {
        "초등학생": "초등학생이 이해할 수 있도록 아주 쉽게 설명해줘.",
        "중학생": "중학생 수준에 맞게 간단하게 설명해줘.",
        "대학생": "대학생 수준에 맞춰 핵심 내용을 요약해줘.",
    }
    if level not in level_map:
        return f"'{level}'은 지원하지 않는 수준입니다. (초등학생, 중학생, 대학생 중 선택)"
    
    prompt = (
        f"다음 뉴스 내용을 {level_map[level]}\n\n 수준으로 다시 설명해줘."
        f"뉴스 내용:\n{text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

# 퀴즈 생성 함수
def make_quiz_with_gemini(text):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        f"다음 뉴스 내용을 바탕으로 객관식 퀴즈 3문제를 만들어줘. "
        f"각 문제는 4개의 선택지와 정답을 포함해야 해. "
        f"아래와 같은 JSON 형식으로 만들어줘. "
        f"문제와 선택지는 최대한 간결하게 작성해줘.\n\n"
        f"[\n"
        f"  {{\n"
        f"    \"question\": \"문제 내용\",\n"
        f"    \"options\": [\"A\", \"B\", \"C\", \"D\"],\n"
        f"    \"answer\": \"정답(보기 내용)\"\n"
        F"    \"explanation\": \"왜 이게 정답인지 간단히 설명해줘.\"\n"
        f"  }},\n"
        f"  ...\n"
        f"]\n\n"
        f"뉴스 내용:\n{text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

# JSON 문자열 정리 함수
def clean_json_string(json_str):
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[len("```json"):].strip()
    if json_str.startswith("```"):
        json_str = json_str[len("```"):].strip()
    if json_str.endswith("```"):
        json_str = json_str[:-3].strip()
    return json_str

# 퀴즈 실행 함수
def run_quiz(quiz_json_str, query=None):
    quiz_json_str = clean_json_string(quiz_json_str)
    try:
        quiz_list = json.loads(quiz_json_str)
    except Exception as e:
        print("퀴즈 데이터 파싱 오류:", e)
        print("원본 데이터:\n", quiz_json_str)
        return

    score = 0
    user_answers = []

    for idx, quiz in enumerate(quiz_list, 1):
        print(f"\n문제 {idx}: {quiz['question']}")
        for i, opt in enumerate(quiz['options']):
            print(f"{chr(65+i)}) {opt}")
        user_ans = input("정답을 입력하세요 (A/B/C/D): ").strip().upper()
        user_answers.append(user_ans)

        try:
            ans_idx = [opt.strip() for opt in quiz['options']].index(quiz['answer'].strip())
            correct = chr(65 + ans_idx)  # 정답의 보기 번호 (A/B/C/D)
        except ValueError:
            print("정답 보기 매칭 오류")
            continue

        if user_ans == correct:
            print("정답입니다!\n")
            score += 1
        else:
            print(f"오답입니다. 정답은 {correct}) {quiz['answer']}입니다.\n")

        explanation = quiz.get("explanation", "").strip()
        if explanation:
            print(f"해설: {explanation}\n")
        else:
            print(f"해설 정보가 없습니다.\n")
            
    print(f"\n총 {len(quiz_list)}문제 중 {score}문제 맞췄습니다.")

    if query:
        save_quiz_results(query, quiz_list, user_answers, score)

# 퀴즈 결과 저장 함수
def save_quiz_results(query, quiz_list, user_answers, score):
    quiz_result_file = Path("summary_outputs") / f"{query}_quiz_result.txt"
    with quiz_result_file.open("w", encoding="utf-8") as f:
        for i, quiz in enumerate(quiz_list):
            f.write(f"[문제 {i+1}]\n{quiz['question']}\n")
            for j, opt in enumerate(quiz['options']):
                f.write(f"  {chr(65+j)}) {opt}\n")
            f.write(f"사용자 선택: {user_answers[i]} / 정답: {quiz['answer']}\n")
            explanation = quiz.get("explanation", "(해설 없음)")
            f.write(f"해설: {explanation}\n\n")
        f.write(f"총 점수: {score} / {len(quiz_list)}\n")
    print(f"[퀴즈 결과 저장 완료] {quiz_result_file}")

# 메인 실행
if __name__ == "__main__":
    query = input("검색할 뉴스 키워드를 입력하세요 (exit 입력 시 종료): ").strip()
    if query.lower() == 'exit':
        print("프로그램을 종료합니다.")
        exit()

    news_item = get_news(query)
    if news_item:
        article_text = get_article_text(news_item)

        # 뉴스 제목, 링크 출력
        print("\n[뉴스 제목]")
        print(news_item['title'])
        print("\n[뉴스 링크]")
        print(news_item['link'])
        print("\n[기사 요약문]\n", article_text)

        # 사용자로부터 설명 수준 입력받기
        level = input("어떤 수준으로 설명해드릴까요? (초등학생 / 중학생 / 대학생): ").strip()
        level_summary = summarize_by_level_with_gemini(level, article_text)
        print(f"\n[{level} 수준 설명]\n{level_summary}")

        # 텍스트 파일 저장
        output_dir = Path("summary_outputs")
        output_dir.mkdir(exist_ok=True)
        full_save_file = output_dir / f"{query}_{level}_full.txt"
        full_save_file.write_text(
            f"[뉴스 제목]\n{news_item['title']}\n\n"
            f"[뉴스 링크]\n{news_item['link']}\n\n"
            f"[기사 요약문]\n{article_text}\n\n"
            f"[{level} 수준 설명]\n{level_summary}",
            encoding="utf-8"
        )
        print(f"[전체 내용 저장 완료] {full_save_file}에 저장되었습니다.")

        # 퀴즈 실행
        quiz_json_str = make_quiz_with_gemini(article_text)
        run_quiz(quiz_json_str, query=query)
