import requests, re, html, urllib.parse, logging
from datetime import datetime, timezone, timedelta
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


def get_press_name(originallink):
    """기사 원본 링크의 도메인을 기반으로 언론사명을 추론하는 함수"""
    try:
        domain = urllib.parse.urlparse(originallink).netloc.replace("www.", "")
    except Exception:
        return "출처 미상"

    for domain_key, press_name in PRESS_DOMAIN_MAP.items():
        if domain_key in domain:
            return press_name

    return domain if domain else "출처 미상"


def tag_cleaner(content):
    """NAVER API 요청 시 발생하는 검색어 강조용 태그들 제거해주는 함수"""
    text = re.sub(r'<[^>]+>', '', content)
    text = html.unescape(text)
    text = text.strip()

    return text


def time_filter(pub_date):
    """검색 시간 범위만큼의 뉴스 기사들만 스크랩하도록 도와주는 함수"""
    date = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
    now = datetime.now(timezone.utc).astimezone(date.tzinfo)

    return (now - date) <= timedelta(hours=NAVER_SEARCH_TIME_RANGE)


def get_naver_news():
    """NAVER API를 이용하여 뉴스의 정보들 가져오는 함수"""
    naver_header = {
        "X-NCP-APIGW-API-KEY-ID": NAVER_CLIENT_ID,
        "X-NCP-APIGW-API-KEY": NAVER_CLIENT_SECRET
    }

    news_list = []

    for keyword in NAVER_KEYWORD:
        # 검색 키워드 / 한 번에 표시할 검색 결과 개수 / 검색 시작 위치 / 정렬 방식 / 응답 형식
        request_query = f"query={keyword}&display={NAVER_NEWS_DISPLAY_NUMBER}&start=1&sort=date&format=json"

        url = f"https://naverapihub.apigw.ntruss.com/search/v1/news?{request_query}"

        try:
            response = requests.get(url, headers=naver_header, timeout=5)
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            logger.error(f"네이버 API 요청 시간 초과 발생: {e}", exc_info=True)
            continue
        except requests.exceptions.RequestException as e:
            logger.error(f"네이버 API요청 실패: {e}", exc_info=True)
            continue

        try:
            result = response.json()
            items = result["items"]
        except (ValueError, KeyError):
            logger.warning("응답 형식 오류 또는 items 값이 존재하지 않음")
            continue

        if not items:
            logger.warning("검색 결과값이 존재하지 않음")
            continue

        for item in items:
            news_list.append({
                "title": tag_cleaner(item["title"]),
                "link": item["link"],
                "originallink": item["originallink"],
                "description": tag_cleaner(item["description"]),
                "pubDate": item["pubDate"],
                "keyword": keyword,
                "source": get_press_name(item["originallink"])
            })

    news_list = [item for item in news_list if time_filter(item["pubDate"])]
    news_list.sort(key=lambda x: datetime.strptime(x["pubDate"], 
                                                   "%a, %d %b %Y %H:%M:%S %z"), 
                                                   reverse=True)

    if not news_list:
        logger.info("최종적으로 수집된 뉴스가 없음")

    return news_list
