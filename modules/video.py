import requests, logging
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


def get_query_for_keyword(keyword):
    """네이버 키워드를 Pexels 검색어로 변환하는 함수"""
    return PEXELS_QUERY_MAP.get(keyword, keyword)


def search_pexels_videos(query, per_page=MINIMUM_VIDEO_COUNT):
    """Pexels API로 세로형(9:16) 스톡 영상을 검색하는 함수"""
    headers = {"Authorization": PEXELS_API_KEY}
    params = {
        "query": query,
        "orientation": "portrait",
        "per_page": per_page
    }

    try:
        response = requests.get(
            "https://api.pexels.com/videos/search",
            headers=headers, params=params, timeout=10
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Pexels API 요청 실패 (query={query}): {e}", exc_info=True)
        return []

    try:
        results = response.json()["videos"]
    except (ValueError, KeyError):
        logger.warning(f"Pexels 응답 파싱 실패 (query={query})")
        return []

    video_urls = []

    for video in results:
        hd_files = [f for f in video["video_files"] if f.get("quality") == "hd" and f["width"] < f["height"]]
        if hd_files:
            video_urls.append(hd_files[0]["link"])

    return video_urls


def download_video(url, save_path):
    """영상 URL을 받아 로컬 파일로 다운로드하는 함수"""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"영상 다운로드 실패 ({url}): {e}", exc_info=True)
        return False

    with open(save_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return True


def ensure_video_pool(keyword):
    """키워드 폴더에 배경 영상이 MINIMUM_VIDEO_COUNT 미만이면 Pexels에서 추가로 받아오는 함수"""
    keyword_dir = Path(ASSETS_PATH) / keyword
    keyword_dir.mkdir(parents=True, exist_ok=True)

    existing_videos = list(keyword_dir.glob("*.mp4"))
    shortage = MINIMUM_VIDEO_COUNT - len(existing_videos)

    if shortage <= 0:
        return

    logger.info(f"[{keyword}] 배경 영상 {shortage}개 부족, Pexels에서 추가 다운로드 시도")

    query = get_query_for_keyword(keyword)
    video_urls = search_pexels_videos(query, per_page=shortage)

    if not video_urls:
        logger.warning(f"[{keyword}] '{query}' 검색 결과 없음")
        return

    downloaded_count = 0
    for idx, url in enumerate(video_urls):
        save_path = keyword_dir / f"{keyword}_{len(existing_videos) + idx + 1}.mp4"
        if download_video(url, save_path):
            downloaded_count += 1
            logger.info(f"[{keyword}] 배경 영상 다운로드 완료: {save_path.name}")

    logger.info(f"[{keyword}] 총 {downloaded_count}개 다운로드 완료")


def get_next_background(keyword):
    """키워드 폴더 안에서 로테이션 방식으로 배경 영상을 선택하는 함수"""
    ensure_video_pool(keyword)

    keyword_dir = Path(ASSETS_PATH) / keyword
    videos = sorted(keyword_dir.glob("*.mp4"))

    if not videos:
        logger.error(f"[{keyword}] 배경 영상이 존재하지 않음 (다운로드 실패 가능성)")
        return None

    index_file = keyword_dir / ".rotation_index"

    try:
        current_index = int(index_file.read_text().strip())
    except (FileNotFoundError, ValueError):
        current_index = 0

    selected = videos[current_index % len(videos)]
    index_file.write_text(str(current_index + 1))

    return selected
