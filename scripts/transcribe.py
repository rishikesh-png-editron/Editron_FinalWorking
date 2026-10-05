#!/usr/bin/env python3
"""
CapGen transcription subprocess — called by Next.js /api/transcribe.

Usage:
    python3 transcribe.py <audio_or_video_file_path> [words_per_caption] [mode]

Outputs JSON to stdout:
    {"success": true, "captions": [...], "language": "en", "language_probability": 0.92, ...}

Uses faster-whisper with word_timestamps=True for real word-level timing.
- For video files (mp4, mov, mkv, webm): extracts audio to WAV via ffmpeg first
- For audio files (mp3, wav, m4a, ogg, aac): passes directly to whisper
Model: tiny (default) — fast on CPU, ~39MB. Override with WHISPER_MODEL_SIZE env var.
"""

import sys
import os
import json
import shutil
import subprocess
import tempfile
import traceback

# Limit threads to avoid sandbox CPU limits
os.environ.setdefault("OMP_NUM_THREADS", "1")

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".flv", ".wmv", ".m4v", ".mpg", ".mpeg"}

# Map CapGen language codes to whisper language hints.
# This helps whisper pick the right decoder for Indic languages (Telugu, Hindi, etc.)
LANG_MAP = {
    "en": "en", "en-US": "en", "en-GB": "en", "en-IN": "en",
    "hi": "hi", "hinglish": "hi",
    "te": "te", "telugish": "te",
    "ta": "ta", "tanglish": "ta",
    "kn": "kn", "kannadish": "kn",
    "ml": "ml", "manglish": "ml",
    "bn": "bn", "bengalish": "bn",
    "pa": "pa", "punjabish": "pa",
    "gu": "gu", "gujaratish": "gu",
    "mr": "mr", "marathish": "mr",
    "or": "or", "odish": "or",
    "ur": "ur",
    "fr": "fr", "de": "de", "es": "es", "pt": "pt", "it": "it",
    "ru": "ru", "ja": "ja", "ko": "ko", "zh": "zh", "ar": "ar",
    "tr": "tr", "nl": "nl", "pl": "pl", "sv": "sv", "id": "id",
    "th": "th", "vi": "vi", "uk": "uk",
}


def extract_audio_to_wav(src_path: str, max_duration_sec: int = 180) -> str | None:
    """Extract audio from a video/audio file to a 16kHz mono WAV using ffmpeg.
    Caps duration at max_duration_sec to avoid timeouts on long videos.
    Returns the path to the temp WAV, or None on failure."""
    if not shutil.which("ffmpeg"):
        return None
    out = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    out.close()
    try:
        result = subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", src_path,
                "-vn",              # no video
                "-ac", "1",         # mono
                "-ar", "16000",     # 16kHz — best for whisper
                "-t", str(max_duration_sec),  # cap duration
                "-f", "wav",
                out.name,
            ],
            capture_output=True,
            timeout=90,
        )
        if result.returncode != 0 or not os.path.exists(out.name) or os.path.getsize(out.name) == 0:
            # Try without duration cap (some ffmpeg versions handle -t differently)
            result2 = subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", src_path,
                    "-vn",
                    "-ac", "1",
                    "-ar", "16000",
                    "-f", "wav",
                    out.name,
                ],
                capture_output=True,
                timeout=120,
            )
            if result2.returncode != 0 or not os.path.exists(out.name) or os.path.getsize(out.name) == 0:
                try:
                    os.unlink(out.name)
                except OSError:
                    pass
                return None
        return out.name
    except subprocess.TimeoutExpired:
        try:
            os.unlink(out.name)
        except OSError:
            pass
        return None
    except Exception:
        try:
            os.unlink(out.name)
        except OSError:
            pass
        return None


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: transcribe.py <file> [words_per_caption] [mode] [language]"}))
        sys.exit(1)

    media_path = sys.argv[1]
    if not os.path.exists(media_path):
        print(json.dumps({"success": False, "error": f"File not found: {media_path}"}))
        sys.exit(1)

    try:
        words_per_caption = int(sys.argv[2]) if len(sys.argv) > 2 else 6
        if words_per_caption < 1:
            words_per_caption = 1
    except (ValueError, TypeError):
        words_per_caption = 6

    mode = sys.argv[3] if len(sys.argv) > 3 else "transcribe"
    if mode not in ("transcribe", "translate"):
        mode = "transcribe"

    # Optional 4th arg: language hint (e.g. "te" for Telugu)
    lang_arg = sys.argv[4] if len(sys.argv) > 4 else ""
    whisper_lang = LANG_MAP.get(lang_arg, None) if lang_arg else None

    # Use "small" model by default — it supports 96+ languages including Telugu,
    # Hindi, Tamil, etc. The "tiny" model is English-only-ish and butchers Indic languages.
    model_size = os.environ.get("WHISPER_MODEL_SIZE", "small")
    beam_size = int(os.environ.get("WHISPER_BEAM_SIZE", "3"))

    # For video AND audio files, extract to a clean 16kHz mono WAV first.
    # This is much more reliable than letting whisper decode containers directly
    # (fixes MP4 failures and standardizes the input).
    ext = os.path.splitext(media_path)[1].lower()
    temp_wav = None
    whisper_input = media_path
    # Always try extraction for video; for audio, only if it's not already a clean wav
    should_extract = ext in VIDEO_EXTS or ext not in {".wav"}
    if should_extract:
        temp_wav = extract_audio_to_wav(media_path)
        if temp_wav:
            whisper_input = temp_wav
        # If extraction failed, fall back to passing the file directly —
        # faster-whisper uses pyav internally and may still decode it.

    try:
        from faster_whisper import WhisperModel

        model = WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=1)

        transcribe_kwargs = {
            "beam_size": beam_size,
            "vad_filter": True,
            "word_timestamps": True,
            "task": mode,
        }
        # Pass language hint if we have one — critical for Telugu/Hindi/Tamil etc.
        # If not provided, whisper will auto-detect from the first 30 seconds.
        if whisper_lang:
            transcribe_kwargs["language"] = whisper_lang

        segments, info = model.transcribe(whisper_input, **transcribe_kwargs)

        all_words = []
        for segment in segments:
            if segment.words:
                all_words.extend(segment.words)

        if not all_words:
            print(json.dumps({
                "success": False,
                "error": "No speech detected in this file. Make sure the audio contains clear speech and is not silent or music-only."
            }))
            sys.exit(0)

        # --- SMART SPLITTING LOGIC START ---
        # We prioritize splitting at punctuation, natural pauses, and conjunctions.

        groups = []
        current_group = []

        # Common conjunctions that are natural split points
        CONJUNCTIONS = {"and", "but", "or", "because", "so", "yet", "for", "nor"}

        i = 0
        while i < len(all_words):
            current_group.append(all_words[i])

            # We check if we should split after the current word.
            # We only start looking for a "smart" split once we have at least 2 words.
            if len(current_group) >= 2:
                # Look ahead window to find the best split point
                # We check the next few words (up to a reasonable limit, e.g., 12)
                best_split_idx = -1
                max_score = -1

                # Check the next few words to see if there's a better place to split
                # than just cutting at words_per_caption.
                search_limit = min(i + 1, i + 12)
                for j in range(i, search_limit):
                    if j >= len(all_words): break

                    word_obj = all_words[j]
                    text = word_obj.word.strip().lower()

                    score = 0
                    # 1. Strong Punctuation (Highest priority)
                    if any(text.endswith(p) for p in (".", "!", "?")):
                        score = 100
                    # 2. Weak Punctuation
                    elif any(text.endswith(p) for p in (",", ";", ":")):
                        score = 50
                    # 3. Natural Pause (gap between words)
                    elif j + 1 < len(all_words):
                        gap = all_words[j+1].start - word_obj.end
                        if gap > 0.6:
                            score = 40
                        elif gap > 0.3:
                            score = 20
                    # 4. Conjunctions
                    if j + 1 < len(all_words):
                        next_text = all_words[j+1].word.strip().lower()
                        if next_text in CONJUNCTIONS:
                            score += 10

                    if score > max_score:
                        max_score = score
                        best_split_idx = j

                # If we've reached the target words_per_caption,
                # or we found a very strong split point (punctuation), we split.
                if len(current_group) >= words_per_caption or (max_score >= 100 and i >= 3):
                    # To avoid splitting too early (e.g., at 2 words),
                    # we only split if we've hit the target or found a hard stop.
                    groups.append(current_group)
                    current_group = []
                elif len(current_group) >= 12: # Hard limit to prevent massive captions
                    groups.append(current_group)
                    current_group = []

            i += 1

        if current_group:
            groups.append(current_group)
        # --- SMART SPLITTING LOGIC END ---

        captions = []
        for group in groups:
            captions.append({
                "start": round(group[0].start, 3),
                "end": round(group[-1].end, 3),
                "text": " ".join(w.word.strip() for w in group).strip(),
            })

        result = {
            "success": True,
            "captions": captions,
            "language": info.language,
            "language_probability": round(info.language_probability, 3),
            "caption_count": len(captions),
            "word_count": len(all_words),
            "mode": mode,
            "model": model_size,
            "input_format": ext.lstrip(".") or "unknown",
            "audio_extracted": temp_wav is not None,
        }
        print(json.dumps(result))

    except Exception as e:
        traceback.print_exc(file=sys.stderr)
        print(json.dumps({"success": False, "error": str(e)}))
        sys.exit(1)

    finally:
        # Clean up temp WAV
        if temp_wav and os.path.exists(temp_wav):
            try:
                os.unlink(temp_wav)
            except OSError:
                pass


if __name__ == "__main__":
    main()
