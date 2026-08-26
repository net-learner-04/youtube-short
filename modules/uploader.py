import pickle, logging
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config import *


Path("logs").mkdir(exist_ok=True)

_module_name = Path(__file__).stem

logger = logging.getLogger(_module_name)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler(f"logs/{_module_name}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]


def get_youtube_client():
    """YouTube Data API v3 인증 후 클라이언트 객체를 반환하는 함수"""
    creds = None
    token_path = Path(YOUTUBE_TOKEN_PATH)

    if token_path.exists():
        with open(token_path, "rb") as token_file:
            creds = pickle.load(token_file)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(YOUTUBE_CLIENT_SECRET_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(token_path, "wb") as token_file:
            pickle.dump(creds, token_file)

    return build("youtube", "v3", credentials=creds)


def build_video_description(news_item):
    """유튜브 설명란에 원본 설명 + 쿠팡 파트너스 고지 문구를 결합하는 함수"""
    base_description = news_item["script"]["youtube_description"]

    if news_item.get("affiliate") is not None:
        return f"{base_description}\n\n{COUPANG_DISCLOSURE_TEXT}"

    return base_description


def upload_video(youtube, news_item):
    """완성된 mp4 파일을 YouTube에 업로드하는 함수"""
    news_id = news_item["audio"]["news_id"]
    script_data = news_item["script"]

    description = build_video_description(news_item)

    body = {
        "snippet": {
            "title": script_data["youtube_title"],
            "description": description,
            "tags": script_data["youtube_tags"],
            "categoryId": YOUTUBE_CATEGORY_ID
        },
        "status": {
            "privacyStatus": YOUTUBE_PRIVACY_STATUS,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(news_item["video_path"], chunksize=-1, resumable=True)

    try:
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        video_id = response["id"]
    except Exception as e:
        logger.error(f"[{news_id}] 영상 업로드 실패: {e}", exc_info=True)
        return None

    logger.info(f"[{news_id}] 업로드 완료 (video_id: {video_id})")

    return video_id


def build_pinned_comment(news_item):
    """제휴 랜딩페이지 URL과 AI 맞춤 CTA를 결합한 고정 댓글 텍스트를 생성하는 함수"""
    affiliate_data = news_item.get("affiliate")

    if affiliate_data is None:
        logger.warning(f"[{news_item['audio']['news_id']}] 제휴 링크 없음, 고정 댓글 생략")
        return None

    keyword = affiliate_data["keyword"]
    landing_url = affiliate_data["landing_url"]

    comment_text = (
        f"오늘 영상에서 소개한 '{keyword}' 관련 상품이 궁금하다면? 👇\n"
        f"{landing_url}\n\n"
        f"구독과 좋아요는 큰 힘이 됩니다 :)\n\n"
        f"{COUPANG_DISCLOSURE_TEXT}"
    )

    return comment_text


def post_pinned_comment(youtube, video_id, comment_text):
    """업로드된 영상에 댓글을 작성하고 고정하는 함수"""
    try:
        comment_response = youtube.commentThreads().insert(
            part="snippet",
            body={
                "snippet": {
                    "videoId": video_id,
                    "topLevelComment": {
                        "snippet": {"textOriginal": comment_text}
                    }
                }
            }
        ).execute()

        comment_id = comment_response["snippet"]["topLevelComment"]["id"]

        youtube.comments().setModerationStatus(
            id=comment_id,
            moderationStatus="published",
        ).execute()

    except Exception as e:
        logger.error(f"댓글 작성/고정 실패 (video_id: {video_id}): {e}", exc_info=True)
        return None

    logger.info(f"video_id {video_id}에 고정 댓글 작성 완료")

    return comment_id


def process_upload(youtube, news_item):
    """기사 1개를 받아 영상 업로드 + 고정 댓글 작성까지 전체 처리하는 함수"""
    news_id = news_item["audio"]["news_id"]

    video_id = upload_video(youtube, news_item)
    if video_id is None:
        return None

    comment_text = build_pinned_comment(news_item)
    if comment_text is not None:
        post_pinned_comment(youtube, video_id, comment_text)

    return video_id


def upload_all(affiliate_results):
    """제휴 링크까지 완성된 기사 리스트를 받아 순차적으로 YouTube에 업로드하는 함수"""
    if not affiliate_results:
        logger.warning("업로드할 영상이 존재하지 않음")
        return []

    youtube = get_youtube_client()

    uploaded = []
    for news_item in affiliate_results:
        video_id = process_upload(youtube, news_item)
        if video_id is not None:
            uploaded.append({**news_item, "youtube_video_id": video_id})

    if len(uploaded) < len(affiliate_results):
        logger.warning(f"요청한 {len(affiliate_results)}개 중 {len(uploaded)}개만 업로드됨")

    return uploaded
