import re, logging
from datetime import datetime
from config import *


logging.basicConfig(filename="select.log",
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def char_bigrams(text):
    """문자열을 공백 제거 후 2글자 단위 집합으로 변환하는 함수"""
    cleaned = re.sub(r"\s+", "", text)

    return set(cleaned[i:i + 2] for i in range(len(cleaned) - 1))


def title_similarity(title_a, title_b):
    """두 기사의 제목을 자카드 유사도 공식으로 계산해서 반환하는 함수"""
    set_a, set_b = char_bigrams(title_a), char_bigrams(title_b)
    if not set_a or not set_b:
        return 0.0

    # 자카드 유사도 = 교집합 크기 / 합집합 크기
    return len(set_a & set_b) / len(set_a | set_b)


def find_function(parent, i):
    """Union-Find: i가 속한 그룹의 대표를 찾음 (경로 압축 적용)."""
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def union_function(parent, i, j):
    """Union-Find: i와 j를 같은 그룹으로 합침."""
    root_i, root_j = find_function(parent, i), find_function(parent, j)
    if root_i != root_j:
        parent[root_j] = root_i


def calculate_duplication_scores(news_list, threshold=SIMILARITY_THRESHOLD):
    """모든 기사 쌍의 제목 유사도를 비교해서 threshold 이상이면 같은 이슈로 묶음."""
    n = len(news_list)
    parent = list(range(n))

    for i in range(n):
        for j in range(i + 1, n):
            if title_similarity(news_list[i]["title"], news_list[j]["title"]) >= threshold:
                union_function(parent, i, j)

    roots = [find_function(parent, i) for i in range(n)]
    group_size = {}
    for root in roots:
        group_size[root] = group_size.get(root, 0) + 1

    return [group_size[root] for root in roots]


def calculate_hot_word_score(news_item):
    """제목 + 설명에 자극성/화제성 단어가 몇 개 포함됐는지 카운트."""
    text = news_item["title"] + " " + news_item["description"]
    return sum(1 for word in HOT_WORDS if word in text)


def calculate_keyword_weight(news_item):
    """config의 NAVER_KEYWORD에서 키워드별 가중치 조회. 정의 안 된 키워드는 1.0."""
    return NAVER_KEYWORD.get(news_item["keyword"], 1.0)


def calculate_freshness_score(news_item):
    """검색 시간 범위(NAVER_SEARCH_TIME_RANGE) 안에서 얼마나 최근인지 0~1로 환산."""
    pub_date = datetime.strptime(news_item["pubDate"], "%a, %d %b %Y %H:%M:%S %z")
    now = datetime.now(pub_date.tzinfo)
    elapsed_hours = (now - pub_date).total_seconds() / 3600
    freshness = 1 - (elapsed_hours / NAVER_SEARCH_TIME_RANGE)
    return max(0.0, min(1.0, freshness))


def calculate_total_score(news_item, duplication_score):
    """개별 점수들을 종합 점수로 합산. 키워드 가중치는 전체에 곱해서 점수 비율 왜곡 없이 반영."""
    hot_score = calculate_hot_word_score(news_item)
    keyword_weight = calculate_keyword_weight(news_item)
    freshness_score = calculate_freshness_score(news_item)

    total = (
        duplication_score * SCORE_WEIGHT_DUPLICATION
        + hot_score * SCORE_WEIGHT_HOT_WORD
        + freshness_score * SCORE_WEIGHT_FRESHNESS
    ) * keyword_weight

    breakdown = {
        "duplication": duplication_score,
        "hot_word": hot_score,
        "keyword_weight": keyword_weight,
        "freshness": round(freshness_score, 2),
    }
    return total, breakdown


def validity_check(news_item, min_title_length=5, min_description_length=20):
    """헤드라인/요약문이 대본 생성에 쓸 만한지 유효성 검증하는 함수"""
    title = news_item["title"].strip()
    description = news_item["description"].strip()

    if len(title) < min_title_length or len(description) < min_description_length:
        return False

    invalid_patterns = ["[포토]", "[영상]", "[사진]", "[알림]"]

    if any(pattern in title for pattern in invalid_patterns):
        return False

    return True


def select_news(news_list, count):
    """중복도, 자극성 단어, 키워드 가중치, 신선도를 종합해서 상위 count개만 선별하는 함수."""
    news_list = [item for item in news_list if validity_check(item)]

    if not news_list:
        logging.warning("선별할 뉴스가 존재하지 않음")
        return []

    duplication_scores = calculate_duplication_scores(news_list)

    scored_news = []
    for idx, news_item in enumerate(news_list):
        total, breakdown = calculate_total_score(news_item, duplication_scores[idx])
        scored_item = {**news_item, "score": round(total, 2), "score_detail": breakdown}
        scored_news.append(scored_item)

        logging.info(
            f"[{news_item['keyword']}] {news_item['title'][:25]}... "
            f"score={scored_item['score']} detail={breakdown}"
        )

    scored_news.sort(key=lambda x: x["score"], reverse=True)
    selected = scored_news[:count]

    if len(selected) < count:
        logging.warning(f"요청한 {count}개보다 적은 {len(selected)}개만 선별됨")

    return selected
