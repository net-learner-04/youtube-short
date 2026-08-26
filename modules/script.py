import json, logging
from openai import OpenAI
from config import *


logging.basicConfig(filename="log/script.log",
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


def build_prompt(news_item):
    """선별된 기사의 제목/요약을 바탕으로 DeepSeek에 보낼 프롬프트를 생성하는 함수"""
    prompt = f"""
다음 뉴스 기사를 바탕으로 유튜브 쇼츠용 대본을 작성해줘.

[기사 제목]
{news_item["title"]}

[기사 요약]
{news_item["description"]}

[작성 조건]
- 전체 분량은 30~45초 분량 (약 250~350자)
- 구조: 3초 훅(hook) + 본문(body) + 클로징(closing)
- 훅은 시청자가 스크롤을 멈출 만큼 자극적이고 궁금증을 유발해야 함
- 본문은 기사 내용을 국뽕/이슈 소구 톤으로 각색
- 클로징은 시청자의 반응(댓글, 구독)을 유도하는 문장으로 마무리
- 전체 대본을 자막/음성 합성이 가능하도록 문장 단위로 분리해서 리스트로도 제공
- 대본 내용과 자연스럽게 연결될 수 있는 제휴 마케팅 키워드 1개 추천 (예: '밀리터리 캠핑용품', '가성비 K-푸드')
- 유튜브 업로드용 제목, 설명, 태그(5개)도 함께 생성

[출력 형식 - JSON]
{{
    "hook": "훅 문장",
    "body": "본문 문장",
    "closing": "클로징 문장",
    "sentences": ["문장1", "문장2", "..."],
    "affiliate_keyword": "제휴 마케팅 키워드",
    "youtube_title": "유튜브 영상 제목",
    "youtube_description": "유튜브 영상 설명",
    "youtube_tags": ["태그1", "태그2", "태그3", "태그4", "태그5"]
}}
"""
    return prompt.strip()


def ask_deepseek(prompt, system_prompt=SYSTEM_PROMPT):
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2048,
        response_format={
            "type": "json_object"
        }
    )

    return response.choices[0].message.content


def parse_response(raw_response):
    """DeepSeek이 반환한 JSON 문자열을 딕셔너리로 변환하고 필수 키 검증하는 함수"""
    required_keys = [
        "hook", "body", "closing", "sentences",
        "affiliate_keyword", "youtube_title",
        "youtube_description", "youtube_tags"
    ]

    try:
        parsed = json.loads(raw_response)
    except (ValueError, TypeError) as e:
        logging.error(f"DeepSeek 응답 JSON 파싱 실패: {e}", exc_info=True)
        return None

    missing_keys = [key for key in required_keys if key not in parsed]

    if missing_keys:
        logging.warning(f"응답에 필수 키 누락: {missing_keys}")
        return None

    return parsed


def generate_script(news_item):
    """기사 1개를 받아 프롬프트 생성 -> DeepSeek 호출 -> 파싱까지 처리하는 함수"""
    prompt = build_prompt(news_item)

    try:
        raw_response = ask_deepseek(prompt)
    except Exception as e:
        logging.error(f"DeepSeek API 요청 실패: {e}", exc_info=True)
        return None

    parsed = parse_response(raw_response)

    if parsed is None:
        logging.warning(f"[{news_item['keyword']}] {news_item['title'][:25]}... 대본 생성 실패")
        return None

    logging.info(f"[{news_item['keyword']}] {news_item['title'][:25]}... 대본 생성 완료")

    return {**news_item, "script": parsed}


def get_scripts(selected_news):
    """선별된 기사 리스트를 받아 기사별로 대본을 생성해 리스트로 반환하는 함수"""
    if not selected_news:
        logging.warning("대본을 생성할 기사가 존재하지 않음")
        return []

    scripts = []

    for news_item in selected_news:
        result = generate_script(news_item)
        if result is not None:
            scripts.append(result)

    if len(scripts) < len(selected_news):
        logging.warning(f"요청한 {len(selected_news)}개 중 {len(scripts)}개만 대본 생성됨")

    return scripts
