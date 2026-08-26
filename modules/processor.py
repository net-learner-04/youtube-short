import subprocess, logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import *


logging.basicConfig(filename="processor.log",
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")


def get_background_videos():
    """storage/assets 폴더에서 배경 루프 영상 목록을 정렬해서 가져오는 함수"""
    assets_dir = Path(ASSETS_PATH)
    videos = sorted(assets_dir.glob("*.mp4"))

    if not videos:
        logging.error("배경 루프 영상이 storage/assets 폴더에 존재하지 않음")

    return videos


def get_next_background():
    """로테이션 방식으로 배경 루프 영상을 순서대로 선택하는 함수 (DB 없이 인덱스 파일로 관리)"""
    videos = get_background_videos()

    if not videos:
        return None

    index_file = Path(ASSETS_PATH) / ".rotation_index"

    try:
        current_index = int(index_file.read_text().strip())
    except (FileNotFoundError, ValueError):
        current_index = 0

    selected = videos[current_index % len(videos)]
    index_file.write_text(str(current_index + 1))

    return selected


def create_title_card(news_item):
    """뉴스 헤드라인을 상단에 고정 노출할 반투명 타이틀 카드 PNG를 생성하는 함수"""
    card = Image.new("RGBA", (VIDEO_WIDTH, VIDEO_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    font = ImageFont.truetype(FONT_PATH, TITLE_CARD_FONT_SIZE)

    title = news_item["title"]
    lines = wrap_text(title, font, draw, max_width=VIDEO_WIDTH - 80)

    box_height = 60 + len(lines) * (TITLE_CARD_FONT_SIZE + 20)
    draw.rectangle([(0, 0), (VIDEO_WIDTH, box_height)], fill=TITLE_CARD_BOX_COLOR)

    y = 30
    
    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (VIDEO_WIDTH - text_width) / 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += TITLE_CARD_FONT_SIZE + 20

    output_path = Path(news_item["audio"]["audio_dir"]) / "title_card.png"
    card.save(output_path)

    return output_path


def wrap_text(text, font, draw, max_width):
    """긴 헤드라인을 타이틀 카드 너비에 맞게 줄바꿈하는 함수"""
    words = text.split()
    lines, current_line = [], ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if draw.textlength(test_line, font=font) <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def seconds_to_ass_time(seconds):
    """초 단위 float 값을 ASS 자막 포맷(H:MM:SS.cc)으로 변환하는 함수"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centiseconds = int((seconds - int(seconds)) * 100)

    return f"{hours}:{minutes:02d}:{secs:02d}.{centiseconds:02d}"


def build_subtitle_file(news_item):
    """오디오 문장별 재생시간을 기준으로 .ass 자막 파일을 생성하는 함수"""
    audio_dir = Path(news_item["audio"]["audio_dir"])
    ass_path = audio_dir / "subtitle.ass"

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV
Style: Default,{SUBTITLE_FONT_NAME},{SUBTITLE_FONT_SIZE},&H00FFFFFF,&H00000000,1,1,4,0,2,150

[Events]
Format: Layer, Start, End, Style, Text
"""

    lines = []
    elapsed = 0.0

    for sentence in news_item["audio"]["sentences"]:
        start = seconds_to_ass_time(elapsed)
        end = seconds_to_ass_time(elapsed + sentence["duration"])
        text = sentence["text"].replace("\n", " ")
        lines.append(f"Dialogue: 0,{start},{end},Default,{text}")
        elapsed += sentence["duration"]

    ass_path.write_text(header + "\n".join(lines), encoding="utf-8")

    return ass_path


def concat_audio(news_item):
    """문장별 mp3 파일들을 하나의 오디오 트랙으로 병합하는 함수"""
    audio_dir = Path(news_item["audio"]["audio_dir"])
    filelist_path = audio_dir / "filelist.txt"
    merged_path = audio_dir / "merged.mp3"

    filelist_content = "\n".join(
        f"file '{Path(sentence['file']).resolve()}'"
        for sentence in news_item["audio"]["sentences"]
    )
    filelist_path.write_text(filelist_content)

    command = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(filelist_path),
        "-c", "copy",
        str(merged_path)
    ]

    try:
        subprocess.run(command, capture_output=True, text=True, timeout=30, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error(f"오디오 병합 실패 ({news_item['audio']['news_id']}): {e}", exc_info=True)
        return None

    return merged_path


def render_video(news_item, background_path, title_card_path, subtitle_path, audio_path):
    """배경 영상 + 타이틀 카드 + 자막 + 오디오를 합성해 QSV 하드웨어 가속으로 최종 렌더링하는 함수"""
    news_id = news_item["audio"]["news_id"]
    output_path = Path(PROCESSED_PATH) / f"{news_id}.mp4"
    duration = news_item["audio"]["total_duration"]

    filter_complex = (
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={VIDEO_WIDTH}:{VIDEO_HEIGHT},setsar=1[bg];"
        f"[bg][1:v]overlay=0:0[titled];"
        f"[titled]ass={subtitle_path}[vout]"
    )

    command = [
        "ffmpeg", "-y",
        "-stream_loop", "-1", "-i", str(background_path),
        "-i", str(title_card_path),
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "2:a",
        "-c:v", "h264_qsv", "-preset", "veryfast",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        str(output_path)
    ]

    try:
        subprocess.run(command, capture_output=True, text=True, timeout=120, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logging.error(f"영상 렌더링 실패 ({news_id}): {e}", exc_info=True)
        return None

    logging.info(f"[{news_id}] 영상 렌더링 완료: {output_path}")

    return output_path


def process_video(news_item):
    """기사 1개를 받아 타이틀 카드/자막/오디오 병합/렌더링까지 전체 처리하는 함수"""
    news_id = news_item["audio"]["news_id"]

    background_path = get_next_background()
    if background_path is None:
        return None

    title_card_path = create_title_card(news_item)
    subtitle_path = build_subtitle_file(news_item)
    audio_path = concat_audio(news_item)

    if audio_path is None:
        logging.warning(f"[{news_id}] 오디오 병합 실패로 렌더링 스킵")
        return None

    video_path = render_video(news_item, background_path, title_card_path, subtitle_path, audio_path)

    return video_path


def get_videos(audio_results):
    """오디오까지 생성된 기사 리스트를 받아 기사별로 최종 shorts.mp4를 렌더링하는 함수"""
    if not audio_results:
        logging.warning("영상을 렌더링할 오디오 결과가 존재하지 않음")
        return []

    results = []

    for news_item in audio_results:
        video_path = process_video(news_item)

        if video_path is not None:
            results.append({**news_item, "video_path": str(video_path)})

    if len(results) < len(audio_results):
        logging.warning(f"요청한 {len(audio_results)}개 중 {len(results)}개만 렌더링됨")

    return results
