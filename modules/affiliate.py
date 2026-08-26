import hmac, hashlib, time, urllib.parse, requests, logging
from datetime import datetime, timezone
from config import *
from pathlib import Path

Path("logs").mkdir(exist_ok=True)

logging.basicConfig(filename="log/affiliate.log",
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def generate_hmac_signature(method, url_path):
    """쿠팡 파트너스 API 인증에 필요한 HMAC 서명을 생성하는 함수"""
    signed_date = datetime.now(timezone.utc).strftime("%y%m%dT%H%M%SZ")
    message = signed_date + method + url_path

    signature = hmac.new(
        COUPANG_SECRET_KEY.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    authorization = (
        f"CEA algorithm=HmacSHA256, access-key={COUPANG_ACCESS_KEY}, "
        f"signed-date={signed_date}, signature={signature}"
    )

    return authorization


def build_search_url(keyword):
    """제휴 키워드를 쿠팡 검색결과 URL로 변환하는 함수"""
    encoded_keyword = urllib.parse.quote(keyword)
    return f"{COUPANG_DOMAIN}/np/search?q={encoded_keyword}"


def convert_to_deeplink(coupang_url):
    """쿠팡 검색결과 URL을 파트너스 딥링크(단축 URL)로 변환하는 함수"""
    url_path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
    authorization = generate_hmac_signature("POST", url_path)

    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json"
    }
    payload = {"coupangUrls": [coupang_url]}

    try:
        response = requests.post(
            f"{COUPANG_API_DOMAIN}{url_path}",
            headers=headers,
            json=payload,
            timeout=5
        )
        response.raise_for_status()
    except requests.exceptions.Timeout as e:
        logging.error(f"쿠팡 API 요청 시간 초과: {e}", exc_info=True)
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"쿠팡 API 요청 실패: {e}", exc_info=True)
        return None

    try:
        result = response.json()
        shorten_url = result["data"][0]["shortenUrl"]
    except (ValueError, KeyError, IndexError) as e:
        logging.error(f"쿠팡 API 응답 파싱 실패: {e}", exc_info=True)
        return None

    return shorten_url


def build_landing_page_url(news_id, keyword, affiliate_link):
    """섀도우밴 방지용 자체 랜딩페이지 URL을 구성하는 함수"""
    encoded_target = urllib.parse.quote(affiliate_link, safe="")
    encoded_keyword = urllib.parse.quote(keyword)

    landing_url = (
        f"{LANDING_PAGE_BASE_URL}/go"
        f"?id={news_id}&kw={encoded_keyword}&target={encoded_target}"
    )

    return landing_url


def get_affiliate_link(news_item):
    """기사 1개를 받아 제휴 키워드 -> 검색 URL -> 딥링크 -> 랜딩페이지까지 처리하는 함수"""
    news_id = news_item["audio"]["news_id"]
    keyword = news_item["script"]["affiliate_keyword"]

    search_url = build_search_url(keyword)
    affiliate_link = convert_to_deeplink(search_url)

    if affiliate_link is None:
        logging.warning(f"[{news_id}] '{keyword}' 딥링크 생성 실패")
        return None

    landing_url = build_landing_page_url(news_id, keyword, affiliate_link)

    logging.info(f"[{news_id}] '{keyword}' 제휴 링크 생성 완료: {landing_url}")

    return {
        "keyword": keyword,
        "search_url": search_url,
        "affiliate_link": affiliate_link,
        "landing_url": landing_url
    }


def get_affiliates(video_results):
    """영상까지 완성된 기사 리스트를 받아 기사별로 제휴 링크를 생성해 붙이는 함수"""
    if not video_results:
        logging.warning("제휴 링크를 생성할 영상 결과가 존재하지 않음")
        return []

    results = []
    for news_item in video_results:
        affiliate_result = get_affiliate_link(news_item)
        results.append({**news_item, "affiliate": affiliate_result})

        if affiliate_result is None:
            time.sleep(0.5)

    return results
