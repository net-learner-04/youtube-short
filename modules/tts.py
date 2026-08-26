import asyncio, subprocess, json, logging
from pathlib import Path
from datetime import datetime
import edge_tts
from config import *


logging.basicConfig(filename="log/tts.log",
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def generate_news_id(news_item):
    """뉴스 기사 단위로 오디오 폴더를 구분하기 위한 고유 ID 생성 함수"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    return f"{timestamp}_{news_item['keyword']}"


async def synthesize_sentence(text, output_path, voice=TTS_VOICE):
    """edge-tts로 문장 1개를 mp3 파일로 합성하는 함수"""
    communicate = edge_tts.Communicate(text, voice)

    await communicate.save(str(output_path))


def get_duration(file_path):
    """ffprobe를 이용해 mp3 파일의 재생시간(초)을 계산하는 함수"""
    command = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        str(file_path)
    ]

    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10, check=True)
        duration = float(json.loads(result.stdout)["format"]["duration"])
        return round(duration, 2)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError, KeyError) as e:
        logging.error(f"재생시간 계산 실패 ({file_path}): {e}", exc_info=True)
        return None


async def synthesize_script(news_item):
    """script.py가 생성한 문장 리스트를 문장별 mp3로 합성하고 재생시간을 계산하는 함수"""
    news_id = generate_news_id(news_item)
    audio_dir = Path(AUDIO_PATH) / news_id
    audio_dir.mkdir(parents=True, exist_ok=True)

    sentences = news_item["script"]["sentences"]
    audio_sentences = []

    for idx, sentence in enumerate(sentences, start=1):
        file_path = audio_dir / f"{idx:02d}.mp3"

        try:
            await synthesize_sentence(sentence, file_path)
        except Exception as e:
            logging.error(f"[{news_id}] {idx}번 문장 TTS 생성 실패: {e}", exc_info=True)
            continue

        duration = get_duration(file_path)

        if duration is None:
            continue

        audio_sentences.append({
            "text": sentence,
            "file": str(file_path),
            "duration": duration
        })

        logging.info(f"[{news_id}] {idx}번 문장 생성 완료 (재생시간: {duration}초)")

    if len(audio_sentences) < len(sentences):
        logging.warning(f"[{news_id}] {len(sentences)}개 중 {len(audio_sentences)}개만 생성됨")

    return {
        "news_id": news_id,
        "audio_dir": str(audio_dir),
        "sentences": audio_sentences,
        "total_duration": round(sum(s["duration"] for s in audio_sentences), 2)
    }


async def get_audio(scripts):
    """대본이 포함된 기사 리스트를 받아 기사별로 오디오를 생성해 리스트로 반환하는 함수"""
    if not scripts:
        logging.warning("오디오를 생성할 대본이 존재하지 않음")
        return []

    results = []

    for news_item in scripts:
        audio_result = await synthesize_script(news_item)
        results.append({**news_item, "audio": audio_result})

    return results
