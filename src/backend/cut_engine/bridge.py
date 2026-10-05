import os
import subprocess
import json
import sys
from pathlib import Path

# Add the current directory to sys.path to allow absolute imports
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from audio import extract_wav_16k_mono, probe_duration
from silence import detect_silences
from plan import build_plan
from render import render
from deps import check_ffmpeg

def process_video(input_path: str, output_dir: str, preset: str = "talk", speed: float = 1.0):
    """
    The main entry point for the Cut Engine.
    Takes a raw video, removes silences and fillers, and returns the tightened video.
    """
    try:
        # 0. Verify Dependencies (FFmpeg)
        ffmpeg_bin, ffprobe_bin = check_ffmpeg()

        # 1. Setup workspace
        stem = os.path.splitext(os.path.basename(input_path))[0]
        work_dir = os.path.join(output_dir, stem, ".work")
        os.makedirs(work_dir, exist_ok=True)

        audio_path = os.path.join(work_dir, "audio_16k.wav")

        # 2. Extract Audio
        extract_wav_16k_mono(ffmpeg_bin, Path(input_path), Path(audio_path))
        duration = probe_duration(ffprobe_bin, Path(input_path))

        # 3. Detect Silences
        silences_fine = detect_silences(Path(audio_path), ffmpeg_bin, noise_db=-40.0, min_dur=0.15)
        silences_coarse = detect_silences(Path(audio_path), ffmpeg_bin, noise_db=-35.0, min_dur=0.25)

        # 4. Build Cut Plan
        cut_plan = build_plan(
            source=input_path,
            duration=duration,
            words=[],
            silences_coarse=silences_coarse,
            silences_fine=silences_fine,
            language="en",
            cut_fillers=False
        )

        # 5. Render tightened video
        output_video_path = os.path.join(output_dir, stem, f"{stem}_cut.mp4")
        os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

        render(
            ffmpeg=ffmpeg_bin,
            src=Path(input_path),
            dst=Path(output_video_path),
            keep=cut_plan.keep,
            speed=speed
        )

        # FIX: Convert the CutPlan object to a dictionary before returning.
        # Python's json.dumps cannot serialize a dataclass directly.
        return {
            "success": True,
            "output_path": output_video_path,
            "cut_plan": {
                "source": cut_plan.source,
                "duration": cut_plan.duration,
                "keep": cut_plan.keep,
                "removed": [
                    {"kind": r.kind, "start": r.start, "end": r.end, "note": r.note}
                    for r in cut_plan.removed
                ]
            },
            "original_duration": duration
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python bridge.py <input_path> <output_dir>")
        sys.exit(1)

    res = process_video(sys.argv[1], sys.argv[2])
    print(json.dumps(res))
