import subprocess, logging
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from modules.video import get_background_sequence
from config import *


Path("logs").mkdir(exist_ok=True)

_module_name = Path(__file__).stem

logger = logging.getLogger(_module_name)
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler(f"logs/{_module_name}.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)


def create_title_card(news_item):
    """뉴스 헤드라인을 담은 상단 고정 헤더 카드(불투명 검정 바) PNG를 생성하는 함수"""
    card = Image.new("RGBA", (VIDEO_WIDTH, HEADER_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rectangle([(0, 0), (VIDEO_WIDTH, HEADER_HEIGHT)], fill=TITLE_CARD_BOX_COLOR)

    font = ImageFont.truetype(FONT_PATH, TITLE_CARD_FONT_SIZE)
    title = news_item["title"]
    lines = wrap_text(title, font, draw, max_width=VIDEO_WIDTH - 80)

    line_height = TITLE_CARD_FONT_SIZE + 20
    total_text_height = len(lines) * line_height - 20
    y = (HEADER_HEIGHT - total_text_height) / 2

    for line in lines:
        text_width = draw.textlength(line, font=font)
        x = (VIDEO_WIDTH - text_width) / 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))
        y += line_height

    output_path = Path(news_item["audio"]["audio_dir"]) / "title_card.png"
    card.save(output_path)

    return output_path


def create_footer_card(news_item):
    """영상 하단 고정 푸터 카드(불투명 검정 바, 출처 표기) PNG를 생성하는 함수"""
    card = Image.new("RGBA", (VIDEO_WIDTH, FOOTER_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(card)
    draw.rectangle([(0, 0), (VIDEO_WIDTH, FOOTER_HEIGHT)], fill=FOOTER_BOX_COLOR)

    font = ImageFont.truetype(FONT_PATH, SOURCE_FONT_SIZE)
    source_text = f"출처: {news_item.get('source', '출처 미상')}"
    text_width = draw.textlength(source_text, font=font)
    x = (VIDEO_WIDTH - text_width) / 2
    draw.text((x, 30), source_text, font=font, fill=(200, 200, 200, 255))

    output_path = Path(news_item["audio"]["audio_dir"]) / "footer_card.png"
    card.save(output_path)

    return output_path


def wrap_text(text, font, draw, max_width):
    """긴 텍스트를 지정된 너비에 맞게 줄바꿈하는 함수"""
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
    """오디오 문장별 재생시간을 기준으로, 푸터 영역 안에 위치할 .ass 자막 파일을 생성하는 함수"""
    audio_dir = Path(news_item["audio"]["audio_dir"])
    ass_path = audio_dir / "subtitle.ass"

    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {VIDEO_WIDTH}
PlayResY: {VIDEO_HEIGHT}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, Bold, BorderStyle, Outline, Shadow, Alignment, MarginV
Style: Default,{SUBTITLE_FONT_NAME},{SUBTITLE_FONT_SIZE},&H00FFFFFF,&H00000000,1,1,4,0,2,{SUBTITLE_MARGIN_V}

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

    result = subprocess.run(command, capture_output=True, text=True, timeout=30)

    if result.returncode != 0:
        logger.error(f"오디오 병합 실패 ({news_item['audio']['news_id']})\nSTDERR:\n{result.stderr}")
        return None

    return merged_path


def render_video(news_item, background_sequence, header_path, footer_path, subtitle_path, audio_path):
    """여러 배경 영상을 이어붙이고, 헤더/푸터/자막/오디오를 합성해 최종 렌더링하는 함수"""
    news_id = news_item["audio"]["news_id"]
    output_path = Path(PROCESSED_PATH) / f"{news_id}.mp4"
    duration = news_item["audio"]["total_duration"]
    video_area_height = VIDEO_HEIGHT - HEADER_HEIGHT - FOOTER_HEIGHT

    command = ["ffmpeg", "-y"]

    for clip in background_sequence:
        command += ["-i", str(clip["path"])]

    header_idx = len(background_sequence)
    footer_idx = header_idx + 1
    audio_idx = footer_idx + 1

    command += ["-i", str(header_path), "-i", str(footer_path), "-i", str(audio_path)]

    filter_parts = []
    concat_labels = ""

    for i in range(len(background_sequence)):
        filter_parts.append(
            f"[{i}:v]scale={VIDEO_WIDTH}:{video_area_height}:force_original_aspect_ratio=increase,"
            f"crop={VIDEO_WIDTH}:{video_area_height},setsar=1,fps=30[v{i}]"
        )
        concat_labels += f"[v{i}]"

    filter_parts.append(f"{concat_labels}concat=n={len(background_sequence)}:v=1:a=0[vidconcat]")
    filter_parts.append(f"color=black:s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:d={duration}[canvas]")
    filter_parts.append(f"[canvas][vidconcat]overlay=0:{HEADER_HEIGHT}[bg1]")
    filter_parts.append(f"[bg1][{header_idx}:v]overlay=0:0[bg2]")
    filter_parts.append(f"[bg2][{footer_idx}:v]overlay=0:{VIDEO_HEIGHT - FOOTER_HEIGHT}[bg3]")
    filter_parts.append(f"[bg3]ass={subtitle_path}[vout]")

    filter_complex = ";".join(filter_parts)

    command += [
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", f"{audio_idx}:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-t", str(duration),
        str(output_path)
    ]

    result = subprocess.run(command, capture_output=True, text=True, timeout=180)

    if result.returncode != 0:
        logger.error(f"영상 렌더링 실패 ({news_id})\nSTDERR:\n{result.stderr}")
        return None

    logger.info(f"[{news_id}] 영상 렌더링 완료: {output_path}")

    return output_path


def process_video(news_item):
    """기사 1개를 받아 헤더/푸터/자막/오디오/배경시퀀스까지 전체 처리하는 함수"""
    news_id = news_item["audio"]["news_id"]
    duration = news_item["audio"]["total_duration"]

    background_sequence = get_background_sequence(news_item["keyword"], duration)
    if not background_sequence:
        return None

    header_path = create_title_card(news_item)
    footer_path = create_footer_card(news_item)
    subtitle_path = build_subtitle_file(news_item)
    audio_path = concat_audio(news_item)

    if audio_path is None:
        logger.warning(f"[{news_id}] 오디오 병합 실패로 렌더링 스킵")
        return None

    video_path = render_video(news_item, background_sequence, header_path, footer_path, subtitle_path, audio_path)

    return video_path


def get_videos(audio_results):
    """오디오까지 생성된 기사 리스트를 받아 기사별로 최종 shorts.mp4를 렌더링하는 함수"""
    if not audio_results:
        logger.warning("영상을 렌더링할 오디오 결과가 존재하지 않음")
        return []

    results = []

    for news_item in audio_results:
        video_path = process_video(news_item)

        if video_path is not None:
            results.append({**news_item, "video_path": str(video_path)})

    if len(results) < len(audio_results):
        logger.warning(f"요청한 {len(audio_results)}개 중 {len(results)}개만 렌더링됨")

    return results
