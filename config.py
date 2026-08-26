import dotenv, os
from pathlib import Path


BASE_DIR = Path(__file__).parent
dotenv.load_dotenv(Path(__file__).parent / ".env")

# 테스트 중엔 True로 설정 (제휴 링크 생성 및 유튜브 업로드를 건너뛰고 영상 생성까지만 확인)
TEST_MODE = True

# 네이버 API 관련 KEYS
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")
NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")

# 좀 더 집중적으로 볼 뉴스 관련 키워드 목록
HOT_WORDS = [
    "역대", "최초", "충격", "발칵", "논란", "화제", "긴급", "속보",
    "단독", "이례적", "경악", "반전", "깜짝", "초유", "열광", "폭주"
]

# 원하는 키워드 입력 (가중치는 1.0으로 고정)
NAVER_KEYWORD = {
    "방산": 1.0,
    "kpop": 1.0,
    "전통": 1.0,
    "이재명": 1.0,
    "케이팝": 1.0,
}

# 키워드 별로 뽑아올 뉴스 개수 입력
NAVER_NEWS_DISPLAY_NUMBER = 1

# 단위: 시간 (시간 범위에 해당하는 뉴스 기사들만 가져옴)
NAVER_SEARCH_TIME_RANGE = 1

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# 발급 콘솔에서 정확한 모델명 확인 후 입력
DEEPSEEK_MODEL = "deepseek-v4-flash"

# 시스템 프롬프트에 작성할 값으로 인공지능이 수행해야 할 역할 입력
SYSTEM_PROMPT = "국뽕 쇼츠 대본 작가"

# 하루에 생성할 영상 개수 입력
DAILY_VIDEO_COUNT = 5

# 제목 유사도로 이슈 분류에 사용 (0.45 이상이면 같은 이슈로 판단)
SIMILARITY_THRESHOLD = 0.45
SCORE_WEIGHT_DUPLICATION = 2.0
SCORE_WEIGHT_HOT_WORD = 3.0
SCORE_WEIGHT_FRESHNESS = 5.0

# edge-tts 한국어 아나운서 톤 음성 (남성: InJoonNeural / 여성: SunHiNeural)
TTS_VOICE = "ko-KR-SunHiNeural"

# 영상 생성에 필요한 자원 파일 저장 경로들
AUDIO_PATH = str(BASE_DIR / "storage" / "audio")
ASSETS_PATH = str(BASE_DIR / "storage" / "assets")
PROCESSED_PATH = str(BASE_DIR / "storage" / "processed")
# 한글 지원 폰트 저장 경로 (실행 전 파일명 정확히 입력)
FONT_PATH = str(BASE_DIR / "storage" / "assets" / ".ttf")

# 비디오 환경 설정
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
TITLE_CARD_FONT_SIZE = 60
TITLE_CARD_BOX_COLOR = (0, 0, 0, 160)
# ffmpeg ass 필터가 시스템에서 찾을 폰트명
SUBTITLE_FONT_NAME = ""
SUBTITLE_FONT_SIZE = 64

# 쿠팡 API KEYS
COUPANG_ACCESS_KEY = os.getenv("COUPANG_ACCESS_KEY")
COUPANG_SECRET_KEY = os.getenv("COUPANG_SECRET_KEY")
COUPANG_DOMAIN = "https://www.coupang.com"
COUPANG_API_DOMAIN = "https://api-gateway.coupang.com"
# 랜딩 페이지 URL
LANDING_PAGE_BASE_URL = "https://"

YOUTUBE_CLIENT_SECRET_PATH = "client_secret.json"
YOUTUBE_TOKEN_PATH = "youtube_token.pickle"
 # 뉴스/정치 카테고리 번호
YOUTUBE_CATEGORY_ID = "25"
YOUTUBE_PRIVACY_STATUS = "public"

# db 파일 경로
DB_PATH = str(BASE_DIR / "storage" / "db" / "news_history.db")

# 쿠팡 전용 유튜브 고정 댓글 포맷
COUPANG_DISCLOSURE_TEXT = "이 영상은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받을 수 있습니다."
