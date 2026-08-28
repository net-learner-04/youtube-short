import asyncio
from modules.fetcher import get_naver_news
from modules.selector import select_news
from modules.script import get_scripts
from modules.tts import get_audio
from modules.processor import get_videos
from modules.affiliate import get_affiliates
from modules.uploader import upload_all
from modules.db import init_db, filter_new_news, save_processed_news
from config import DAILY_VIDEO_COUNT, TEST_MODE


async def main():
    init_db()

    news = get_naver_news()
    news = filter_new_news(news)

    selected = select_news(news, DAILY_VIDEO_COUNT)

    for item in selected:
        print(item["score"], item["score_detail"], item["title"])

    scripts = get_scripts(selected)
    audio_results = await get_audio(scripts)
    video_results = get_videos(audio_results)

    for item in video_results:
        print(f"\n영상 생성 완료: {item['video_path']}\n")

    if TEST_MODE:
        print("TEST_MODE=True 이므로 제휴 링크 생성 및 업로드는 건너뜁니다.\n")
        return video_results

    affiliate_results = get_affiliates(video_results)
    uploaded = upload_all(affiliate_results)

    for item in uploaded:
        save_processed_news(item)
        print(f"업로드 완료: {item['script']['youtube_title']} (video_id: {item['youtube_video_id']})\n")

    return uploaded


if __name__ == "__main__":
    asyncio.run(main())
