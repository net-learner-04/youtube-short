import json, logging
from openai import OpenAI
from pathlib import Path
from config import *


Path("logs").mkdir(exist_ok=True)

_module_name = Path(__file__).stem

logger = logging.getLogger(_module_name)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler(f"logs/{_module_name}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


def build_prompt(news_item):
    """선별된 기사의 제목/요약을 바탕으로 DeepSeek에 보낼 프롬프트를 생성하는 함수"""
    prompt = f"""
다음 뉴스 기사를 바탕으로 유튜브 쇼츠용 경제 뉴스 대본을 작성해줘.

[기사 제목]
{news_item["title"]}

[기사 요약]
{news_item["description"]}

[작성 조건]
- 전체 분량은 30~45초 분량 (약 250~350자)
- 구조: 3초 훅(hook) + 본문(body) + 클로징(closing)
- 훅은 숫자나 핵심 팩트로 시작해 시청자의 관심을 즉시 끌어야 함 (자극적인 과장보다는 정확한 정보로 궁금증 유발)
- 본문은 신뢰감 있는 경제 전문가의 톤으로, 기사 내용을 명확하고 담백하게 설명. 어려운 경제 용어는 짧게 풀어서 설명하고, 이 소식이 시청자의 자산/소비/생활에 어떤 의미인지 짚어줄 것
- 클로징은 냉정한 시각을 담은 한 줄 총평이나 앞으로 지켜봐야 할 포인트로 마무리 (과도한 감탄사나 선정적 표현 지양)
- 전체 대본을 자막/음성 합성이 가능하도록 문장 단위로 분리해서 리스트로도 제공
- 대본 내용과 자연스럽게 연결될 수 있는 제휴 마케팅 키워드 1개 추천 (예: '금 투자', '가계부 앱', '재테크 서적')
- 유튜브 업로드용 제목, 설명, 태그(5개)도 함께 생성. 제목은 자극적인 클릭베이트보다 신뢰도를 주는 정보성 제목으로 작성

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
        max_tokens=4096,
        response_format={
            "type": "json_object"
        },
        extra_body={"thinking": {"type": "disabled"}}
    )

    choice = response.choices[0]
    finish_reason = choice.finish_reason
    content = choice.message.content

    if finish_reason != "stop":
        logger.warning(f"DeepSeek 응답이 정상 종료되지 않음 (finish_reason={finish_reason})")

    return content


def parse_response(raw_response):
    """DeepSeek이 반환한 JSON 문자열을 딕셔너리로 변환하고 필수 키 검증하는 함수"""
    required_keys = [
        "hook", "body", "closing", "sentences",
        "affiliate_keyword", "youtube_title",
        "youtube_description", "youtube_tags"
    ]

    if not raw_response:
        logger.error("DeepSeek 응답이 비어있음 (None 또는 빈 문자열)")
        return None

    try:
        parsed = json.loads(raw_response)
    except (ValueError, TypeError) as e:
        logger.error(f"DeepSeek 응답 JSON 파싱 실패: {e}", exc_info=True)
        logger.error(f"파싱 실패한 원본 응답 (앞 500자): {raw_response[:500]}")
        return None

    missing_keys = [key for key in required_keys if key not in parsed]

    if missing_keys:
        logger.warning(f"응답에 필수 키 누락: {missing_keys}")
        return None

    return parsed


def generate_script(news_item):
    """기사 1개를 받아 프롬프트 생성 -> DeepSeek 호출 -> 파싱까지 처리하는 함수"""
    prompt = build_prompt(news_item)

    try:
        raw_response = ask_deepseek(prompt)
    except Exception as e:
        logger.error(f"DeepSeek API 요청 실패: {e}", exc_info=True)
        return None

    parsed = parse_response(raw_response)

    if parsed is None:
        logger.warning(f"[{news_item['keyword']}] {news_item['title'][:25]}... 대본 생성 실패")
        return None

    logger.info(f"[{news_item['keyword']}] {news_item['title'][:25]}... 대본 생성 완료")

    return {**news_item, "script": parsed}


def get_scripts(selected_news):
    """선별된 기사 리스트를 받아 기사별로 대본을 생성해 리스트로 반환하는 함수"""
    if not selected_news:
        logger.warning("대본을 생성할 기사가 존재하지 않음")
        return []

    scripts = []

    for news_item in selected_news:
        result = generate_script(news_item)
        if result is not None:
            scripts.append(result)

    if len(scripts) < len(selected_news):
        logger.warning(f"요청한 {len(selected_news)}개 중 {len(scripts)}개만 대본 생성됨")

    return scripts
