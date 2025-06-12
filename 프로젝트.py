import urllib.request
import urllib.parse
import json
import google.generativeai as genai

# 네이버 API 정보 입력
client_id = "bU3TXXvjacAeDbXe3Aez"
client_secret = "cOQzRU93bn"

# Gemini API 키 입력
GEMINI_API_KEY = "AIzaSyAktqP3pdrp34uR2u2Mdb5JcJywb3_bpf4"

def get_news(query):
    encText = urllib.parse.quote(query)
    url = f"https://openapi.naver.com/v1/search/news.json?query={encText}&display=1&sort=sim"
    request = urllib.request.Request(url)
    request.add_header("X-Naver-Client-Id", client_id)
    request.add_header("X-Naver-Client-Secret", client_secret)
    response = urllib.request.urlopen(request)
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

def get_article_text(news_item):
    return news_item['description']

def summarize_levels_with_gemini(text):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = (
        f"다음 뉴스 내용을 간단하게 요약해줘.\n"
        f"그리고 초등학생, 중학생, 대학생 수준으로 각각 다시 설명해줘.\n\n"
        f"뉴스 내용:\n{text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

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
        f"  }},\n"
        f"  ...\n"
        f"]\n\n"
        f"뉴스 내용:\n{text}"
    )
    response = model.generate_content(prompt)
    return response.text.strip()

def clean_json_string(json_str):
    json_str = json_str.strip()
    if json_str.startswith("```json"):
        json_str = json_str[len("```json"):].strip()
    if json_str.startswith("```"):
        json_str = json_str[len("```"):].strip()
    if json_str.endswith("```"):
        json_str = json_str[:-3].strip()
    return json_str

def run_quiz(quiz_json_str):
    quiz_json_str = clean_json_string(quiz_json_str)
    try:
        quiz_list = json.loads(quiz_json_str)
    except Exception as e:
        print("퀴즈 데이터 파싱 오류:", e)
        print("원본 데이터:\n", quiz_json_str)
        return

    score = 0
    for idx, quiz in enumerate(quiz_list, 1):
        print(f"\n문제 {idx}: {quiz['question']}")
        for i, opt in enumerate(quiz['options']):
            print(f"{chr(65+i)}) {opt}")
        user_ans = input("정답을 입력하세요 (A/B/C/D): ").strip().upper()
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
    print(f"\n총 {len(quiz_list)}문제 중 {score}문제 맞췄습니다.")

if __name__ == "__main__":
    query = input("검색할 뉴스를 입력하세요: ")
    news_item = get_news(query)
    if news_item:
        article_text = get_article_text(news_item)
        print("\n[기사 요약문]\n", article_text)

        # 수준별 요약 추가
        level_summary = summarize_levels_with_gemini(article_text)
        print("\n[수준별 요약]\n", level_summary)

        quiz_json_str = make_quiz_with_gemini(article_text)
        run_quiz(quiz_json_str)