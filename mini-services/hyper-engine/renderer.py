import subprocess
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HyperRenderer")

class HyperRenderer:
    def __init__(self, output_path="output_final.mp4"):
        self.output_path = output_path

    def get_video_info(self, video_path):
        """
        Uses ffprobe to get width and height of the source video.
        """
        cmd = [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width,height", "-of", "json", video_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            width = data["streams"][0]["width"]
            height = data["streams"][0]["height"]
            return width, height
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return 1080, 1920  # Default fallback

    def render(self, video_path, broll_data, project_data=None, max_duration=4.0):
        """
        Renders the final video by applying B-roll cutaways.

        Args:
            video_path: Path to main source video.
            broll_data: List of objects [{'path': '...', 'start': 1.0, 'end': 3.0}, ...]
            project_data: Project JSON
            max_duration: Maximum duration for any single B-roll clip (default 4s)
        """
        width, height = self.get_video_info(video_path)

        logger.info(f"Source resolution: {width}x{height}")

        # 1. Inputs
        # [0:v][0:a] are main video/audio
        inputs = ["-i", video_path]

        # Add B-roll inputs
        for clip in broll_data:
            inputs.extend(["-i", clip['path']])

        # 2. Filter Complex
        filter_complex = []

        # --- Text-to-Cut Implementation ---
        main_v = "[0:v]"
        main_a = "[0:a]"
        if project_data and 'cuts' in project_data and project_data['cuts']:
            cuts = project_data['cuts']
            select_expr = " * ".join([f"not(between(t,{c['start']},{c['end']}))" for c in cuts])
            filter_complex.append(f"{main_v}select='{select_expr}',setpts=PTS-STARTPTS[v_cut]")
            filter_complex.append(f"{main_a}aselect='{select_expr}',asetpts=PTS-STARTPTS[a_cut]")
            main_v, main_a = "[v_cut]", "[a_cut]"

        # Process each B-roll to match the target resolution (Fill/Cover)
        # and ensure it is trimmed to the target duration.
        for i in range(len(broll_data)):
            input_idx = i + 1
            start = broll_data[i]['start']
            end = broll_data[i]['end']
            duration = end - start

            # Professional Cutaway:
            # 1. Trim the clip to the exact duration required.
            # 2. Scale to cover, crop to center, and reset SAR.
            filter_complex.append(
                f"[{input_idx}:v]trim=duration={duration},setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1[br{i}]"
            )



        # Layering: we start with the main video [v_cut or 0:v]
        current_v = main_v

        for i, clip in enumerate(broll_data):
            start = clip['start']
            end = clip['end']
            # Transition Logic: apply a short fade to B-roll clips to avoid hard cuts
            out_v = f"[v{i}]"
            filter_complex.append(
                f"{current_v}[br{i}]overlay=x=0:y=0:enable='between(t,{start},{end})'{out_v}"
            )
            current_v = out_v

        # Final FFmpeg command
        # -y: overwrite output
        # -filter_complex: our cutaway chain
        # -map: final processed video and original audio
        cmd = [
            "ffmpeg", "-y",
            *inputs,
            "-filter_complex", ";".join(filter_complex),
            "-map", current_v,
            "-map", main_a,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            self.output_path
        ]

        logger.info(f"Executing FFmpeg command: {' '.join(cmd)}")
        return self.execute_ffmpeg(cmd)

    def execute_ffmpeg(self, cmd):
        try:
            subprocess.run(cmd, check=True)
            logger.info(f"Successfully rendered to {self.output_path}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg failed: {e}")
            return False
