import subprocess, logging
from pathlib import Path
from config import *
from modules.db import init_db


Path("logs").mkdir(exist_ok=True)

_module_name = Path(__file__).stem

logger = logging.getLogger(_module_name)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler(f"logs/{_module_name}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)

BASE_DIR = Path(__file__).parent


def create_directories():
    """영상 생성에 필요한 storage 하위 폴더들을 생성하는 함수"""
    directories = [
        Path(AUDIO_PATH),
        Path(ASSETS_PATH),
        Path(PROCESSED_PATH),
        Path(DB_PATH).parent,
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"폴더 준비 완료: {directory}")


def create_env_template():
    """.env 파일이 없으면 필요한 키 목록을 담은 템플릿을 생성하는 함수"""
    env_path = BASE_DIR / ".env"

    if env_path.exists():
        logger.info(".env 파일이 이미 존재하여 건너뜀")
        return

    template = """# Naver Search API
NAVER_CLIENT_ID=
NAVER_CLIENT_SECRET=

# DeepSeek API
DEEPSEEK_API_KEY=

# Coupang Partners API
COUPANG_ACCESS_KEY=
COUPANG_SECRET_KEY=

# Pexels Api Key
PEXELS_API_KEY=
"""

    env_path.write_text(template, encoding="utf-8")
    logger.info(".env 템플릿 파일 생성 완료 - 값을 채워넣어야 함")


def check_font_file():
    """Pillow 타이틀 카드용 한글 폰트 파일(FONT_PATH) 존재 여부를 확인하는 함수"""
    font_path = Path(FONT_PATH)

    if font_path.exists():
        logger.info(f"폰트 파일 확인됨: {font_path}")
    else:
        logger.warning(
            f"폰트 파일이 없습니다: {font_path}\n"
            f"  -> Pretendard, 나눔고딕 등 한글 지원 폰트(.ttf)를 다운받아 "
            f"위 경로에 직접 넣어야 합니다."
        )


def check_subtitle_font():
    """ffmpeg(ass 필터)가 자막에 사용할 SUBTITLE_FONT_NAME이 시스템에 설치돼 있는지 확인하는 함수"""
    try:
        result = subprocess.run(
            ["fc-list"], capture_output=True, text=True, timeout=10, check=True
        )
    except FileNotFoundError:
        logger.warning(
            "fc-list 명령어를 찾을 수 없습니다.\n"
            "  -> fontconfig가 설치되어 있지 않을 수 있습니다: sudo dnf install fontconfig -y"
        )
        return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.error(f"fc-list 실행 실패: {e}", exc_info=True)
        return

    if SUBTITLE_FONT_NAME.lower() in result.stdout.lower():
        logger.info(f"시스템 폰트 확인됨: '{SUBTITLE_FONT_NAME}'")
    else:
        logger.warning(
            f"시스템에 '{SUBTITLE_FONT_NAME}' 폰트가 설치되어 있지 않습니다.\n"
            f"  -> ffmpeg 자막(.ass)이 다른 폰트로 대체되어 렌더링됩니다.\n"
            f"  -> 아래 명령어로 FONT_PATH의 폰트를 시스템에 설치하세요:\n"
            f"     sudo mkdir -p /usr/share/fonts/custom\n"
            f"     sudo cp {FONT_PATH} /usr/share/fonts/custom/\n"
            f"     sudo fc-cache -fv\n"
            f"  -> 설치 후 'fc-list | grep -i \"{SUBTITLE_FONT_NAME}\"'로 정확한 폰트명을 재확인하세요."
        )


def check_background_videos():
    """배경 루프 영상이 assets 폴더에 있는지 확인하는 함수"""
    videos = list(Path(ASSETS_PATH).glob("*.mp4"))

    if videos:
        logger.info(f"배경 루프 영상 {len(videos)}개 확인됨")
    else:
        logger.warning(
            f"배경 루프 영상(.mp4)이 없습니다: {ASSETS_PATH}\n"
            f"  -> 9:16 세로 비율의 배경 영상을 해당 폴더에 넣어야 합니다."
        )


def check_qsv_encoder():
    """FFmpeg에서 h264_qsv 하드웨어 가속 인코더 사용 가능 여부를 확인하는 함수"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-encoders"], capture_output=True, text=True, timeout=10, check=True
        )
    except FileNotFoundError:
        logger.warning("ffmpeg 명령어를 찾을 수 없습니다. -> sudo dnf install ffmpeg -y")
        return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.error(f"ffmpeg -encoders 실행 실패: {e}", exc_info=True)
        return

    if "h264_qsv" in result.stdout:
        logger.info("h264_qsv 하드웨어 가속 인코더 확인됨")
    else:
        logger.warning(
            "h264_qsv 인코더를 찾을 수 없습니다.\n"
            "  -> Intel Media Driver(intel-media-va-driver) 설치 여부를 확인하세요."
        )


def check_client_secret():
    """유튜브 OAuth client_secret.json 파일 존재 여부를 확인하는 함수"""
    client_secret_path = BASE_DIR / YOUTUBE_CLIENT_SECRET_PATH

    if client_secret_path.exists():
        logger.info(f"client_secret.json 확인됨: {client_secret_path}")
    else:
        logger.warning(
            f"client_secret.json이 없습니다: {client_secret_path}\n"
            f"  -> Google Cloud Console에서 OAuth 클라이언트(데스크톱 앱) 발급 후 "
            f"프로젝트 루트에 저장해야 합니다."
        )


def setup():
    """프로젝트 초기 세팅을 한 번에 실행하는 함수"""
    logger.info("===== 프로젝트 초기 세팅 시작 =====")

    create_directories()
    create_env_template()
    init_db()
    check_font_file()
    check_subtitle_font()
    check_background_videos()
    check_qsv_encoder()
    check_client_secret()

    logger.info("===== 초기 세팅 완료 =====")
    logger.info("위 경고(WARNING) 항목이 있다면 실행 전 직접 채워넣어야 합니다.")


if __name__ == "__main__":
    setup()
