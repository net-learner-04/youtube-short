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
    "역대", "최초", "급등", "급락", "폭등", "폭락", "비상",
    "사상 최고", "사상 최저", "발칵", "충격", "경고", "긴급",
    "단독", "이례적", "패닉", "초유", "휘청", "요동"
]

# 원하는 키워드 입력 (가중치는 시장 관심도에 따라 차등)
NAVER_KEYWORD = {
    # 통화정책 / 금리
    "기준금리": 1.0,
    "한국은행": 1.0,
    "연준": 1.0,
    "미국 금리": 1.1,

    # 증시
    "코스피": 1.0,
    "코스닥": 0.9,
    "미국 증시": 1.0,
    "나스닥": 1.0,
    "S&P500": 0.9,

    # 외환
    "환율": 1.2,
    "원달러 환율": 1.0,
    "엔화": 0.8,

    # 원자재 / 에너지
    "국제유가": 1.0,
    "금값": 1.0,
    "원자재 가격": 0.8,

    # 가상자산
    "비트코인": 1.1,
    "암호화폐": 0.9,
    "가상자산": 0.8,

    # 부동산
    "부동산 시장": 1.0,
    "아파트 가격": 0.9,
    "전세 대출": 0.8,

    # 물가 / 소비
    "물가 상승률": 1.1,
    "소비자물가": 1.0,
    "생활물가": 0.9,

    # 산업 / 무역
    "반도체 수출": 1.0,
    "수출입 동향": 0.8,
    "관세": 0.9,

    # 고용 / 거시
    "고용지표": 0.8,
    "GDP 성장률": 0.9,

    # 글로벌 경제 일반
    "글로벌 경제": 0.9,
    "세계 경제": 0.8,
}

# 키워드 별로 뽑아올 뉴스 개수 입력
NAVER_NEWS_DISPLAY_NUMBER = 1

# 단위: 시간 (시간 범위에 해당하는 뉴스 기사들만 가져옴)
NAVER_SEARCH_TIME_RANGE = 1

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# 발급 콘솔에서 정확한 모델명 확인 후 입력
DEEPSEEK_MODEL = "deepseek-v4-flash"

# 시스템 프롬프트에 작성할 값으로 인공지능이 수행해야 할 역할 입력
SYSTEM_PROMPT = "경제/금융 전문 쇼츠 대본 작가"

# 하루에 생성할 영상 개수 입력
DAILY_VIDEO_COUNT = 1

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

# 영상에서 사용할 폰트 위치
FONT_DIR = str(BASE_DIR / "fonts")
FONT_PATH = str(BASE_DIR / "fonts" / "NanumGothic.ttf")

# 비디오 환경 설정
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
TITLE_CARD_FONT_SIZE = 60
# ffmpeg ass 필터가 시스템에서 찾을 폰트명
SUBTITLE_FONT_NAME = "NanumGothic"
SUBTITLE_FONT_SIZE = 64
HEADER_HEIGHT = 260
FOOTER_HEIGHT = 260
SOURCE_FONT_SIZE = 40
SUBTITLE_MARGIN_V = 50
TITLE_CARD_BOX_COLOR = (0, 0, 0, 255)
FOOTER_BOX_COLOR = (0, 0, 0, 255)

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

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

import random

# 네이버 키워드 -> Pexels 검색어 매핑
PEXELS_QUERY_MAP = {
    "기준금리": ["central bank building", "federal reserve building", "bank interest rate", "financial district skyscraper"],
    "한국은행": ["central bank building", "bank of korea", "financial district seoul", "korean won money"],
    "연준": ["federal reserve building", "washington dc government", "central bank meeting", "us capitol building"],
    "미국 금리": ["federal reserve building", "wall street new york", "us dollar bills", "financial district night"],

    "코스피": ["stock market trading floor", "stock chart graph screen", "trading desk monitors", "stock exchange board"],
    "코스닥": ["stock chart graph screen", "trading desk monitors", "stock market ticker", "financial data screen"],
    "미국 증시": ["wall street new york", "stock market ticker", "nyse trading floor", "financial district night"],
    "나스닥": ["stock market trading floor", "tech company office", "stock chart graph screen", "trading desk monitors"],
    "S&P500": ["stock market ticker", "stock chart graph screen", "wall street new york", "financial data screen"],

    "환율": ["currency exchange money", "dollar bills stack", "foreign currency notes", "money exchange booth"],
    "원달러 환율": ["dollar bills stack", "korean won money", "currency exchange money", "money exchange booth"],
    "엔화": ["japanese yen currency", "currency exchange money", "foreign currency notes", "tokyo financial district"],

    "국제유가": ["oil rig ocean", "oil barrel industry", "gas station fuel", "crude oil pipeline"],
    "금값": ["gold bars stack", "gold jewelry shop", "precious metal bullion", "gold mining"],
    "원자재 가격": ["shipping port containers", "industrial factory", "commodity warehouse", "raw materials industry"],

    "비트코인": ["bitcoin cryptocurrency coin", "crypto trading screen", "digital currency concept", "blockchain technology"],
    "암호화폐": ["crypto trading screen", "digital currency concept", "bitcoin cryptocurrency coin", "blockchain technology"],
    "가상자산": ["digital currency concept", "crypto trading screen", "blockchain technology", "bitcoin cryptocurrency coin"],

    "부동산 시장": ["apartment buildings city", "real estate housing", "construction site city", "residential skyline"],
    "아파트 가격": ["apartment buildings city", "residential skyline", "korean apartment complex", "real estate housing"],
    "전세 대출": ["bank building exterior", "real estate housing", "apartment buildings city", "home loan document"],

    "물가 상승률": ["grocery store shopping", "supermarket aisle", "market vegetables prices", "shopping cart groceries"],
    "소비자물가": ["supermarket aisle", "grocery store shopping", "shopping cart groceries", "market vegetables prices"],
    "생활물가": ["market vegetables prices", "grocery store shopping", "supermarket aisle", "shopping cart groceries"],

    "반도체 수출": ["semiconductor factory", "microchip technology", "factory production line", "shipping port containers"],
    "수출입 동향": ["shipping port containers", "cargo ship ocean", "factory production line", "global trade cargo"],
    "관세": ["shipping port containers", "cargo ship ocean", "customs border", "global trade cargo"],

    "고용지표": ["office workers meeting", "job interview office", "business team working", "corporate office building"],
    "GDP 성장률": ["city skyline aerial", "factory production line", "business district buildings", "global economy trade"],

    "글로벌 경제": ["world map globe finance", "container ship port", "global trade cargo", "business meeting office"],
    "세계 경제": ["world map globe finance", "global trade cargo", "container ship port", "business meeting office"],
}

# 매핑에 없는 키워드이거나, 검색 결과가 0개일 때 사용할 범용 대체 검색어
FALLBACK_QUERY_LIST = [
    "stock market chart",
    "city financial district",
    "business office skyline",
    "money finance concept",
    "global economy trade",
]

# 키워드별로 미리 확보해둘 배경 영상 최소 개수 (부족하면 자동으로 더 받아옴)
MINIMUM_VIDEO_COUNT = 8

# originallink 도메인 -> 언론사명 매핑
PRESS_DOMAIN_MAP = {
    "yna.co.kr": "연합뉴스",
    "chosun.com": "조선일보",
    "joongang.co.kr": "중앙일보",
    "joins.com": "중앙일보",
    "hani.co.kr": "한겨레",
    "khan.co.kr": "경향신문",
    "mk.co.kr": "매일경제",
    "hankyung.com": "한국경제",
    "sbs.co.kr": "SBS",
    "kbs.co.kr": "KBS",
    "imbc.com": "MBC",
    "ytn.co.kr": "YTN",
    "news1.kr": "뉴스1",
    "newsis.com": "뉴시스",
    "edaily.co.kr": "이데일리",
    "mt.co.kr": "머니투데이",
    "hankookilbo.com": "한국일보",
    "seoul.co.kr": "서울신문",
    "donga.com": "동아일보",
    "nocutnews.co.kr": "노컷뉴스",
    "jtbc.co.kr": "JTBC",
    "biz.chosun.com": "조선비즈",
    "sedaily.com": "서울경제",
    "fnnews.com": "파이낸셜뉴스",
    "asiae.co.kr": "아시아경제",
    "moneys.co.kr": "머니S",
    "kmib.co.kr": "국민일보",
    "bloter.net": "블로터",
}
