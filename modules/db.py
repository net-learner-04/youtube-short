import sqlite3, logging
from pathlib import Path
from datetime import datetime
from config import *
from pathlib import Path

Path("log").mkdir(exist_ok=True)

logging.basicConfig(filename="log/db.log",
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def get_connection():
    """SQLite DB 파일에 연결하고 커넥션 객체를 반환하는 함수"""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


def init_db():
    """news_history 테이블이 없으면 생성하는 함수"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS news_history (
            link TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            keyword TEXT,
            processed_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def is_already_processed(news_item):
    """기사의 link(고유 URL) 기준으로 이미 영상화된 적 있는지 확인하는 함수"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM news_history WHERE link = ?", (news_item["link"],))
    result = cursor.fetchone()

    conn.close()

    return result is not None


def save_processed_news(news_item):
    """업로드까지 완료된 기사를 이력 테이블에 기록하는 함수"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO news_history (link, title, keyword, processed_at) VALUES (?, ?, ?, ?)",
            (news_item["link"], news_item["title"], news_item["keyword"], datetime.now().isoformat())
        )
        conn.commit()
    except sqlite3.IntegrityError:
        logging.warning(f"이미 기록된 기사 (link 중복): {news_item['link']}")
    finally:
        conn.close()


def filter_new_news(news_list):
    """수집된 기사 리스트에서 이미 처리된 적 있는 기사를 제외하는 함수"""
    if not news_list:
        return []

    filtered = [item for item in news_list if not is_already_processed(item)]

    excluded_count = len(news_list) - len(filtered)
    if excluded_count > 0:
        logging.info(f"이전에 처리된 기사 {excluded_count}개 제외됨")

    return filtered
