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

        # --- Transition Assets ---
        TRANSITION_DIR = r"C:\Users\Rishika\Downloads\Sargam Transition Part-2-20261007T144710Z-1-001\Sargam Transition Part-2"
        TRANS_IN = os.path.join(TRANSITION_DIR, "Projector Glow.mov")
        TRANS_OUT = os.path.join(TRANSITION_DIR, "Analog Burn.mov")
        TRANS_DURATION = 0.3

        # 1. Inputs
        # [0:v][0:a] are main video/audio
        inputs = ["-i", video_path]
        inputs.extend(["-i", TRANS_IN])    # Index 1
        inputs.extend(["-i", TRANS_OUT])  # Index 2

        # Add B-roll inputs starting from Index 3
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
            br_idx = i + 3
            start = broll_data[i]['start']
            end = broll_data[i]['end']
            trim_start = broll_data[i].get('trimStart', 0)
            duration = end - start

            # A. Process the B-roll clip: Trim from trim_start, Scale to Cover, Crop to Center
            filter_complex.append(
                f"[{br_idx}:v]trim=start={trim_start}:duration={duration},setpts=PTS-STARTPTS,scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},setsar=1[br{i}]"
            )

            # B. Process Transition-In: Scale to Cover, Trim to duration, Screen Blend
            filter_complex.append(
                f"[1:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},trim=duration={TRANS_DURATION},setpts=PTS-STARTPTS[tin{i}]"
            )

            # C. Process Transition-Out: Scale to Cover, Trim to duration, Screen Blend
            filter_complex.append(
                f"[2:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},trim=duration={TRANS_DURATION},setpts=PTS-STARTPTS[tout{i}]"
            )



        # Layering: we start with the main video [v_cut or 0:v]
        current_v = main_v
        for i, clip in enumerate(broll_data):
            start = clip['start']
            end = clip['end']

            # we create a sequence: Main -> Trans-In -> B-Roll -> Trans-Out -> Main

            # 1. Transition-In Overlay (Screen Blend)
            t_in_start = max(0, start - TRANS_DURATION)
            t_in_end = start + TRANS_DURATION
            v_in = f"[vin{i}]"
            filter_complex.append(
                f"{current_v}[tin{i}]blend=all_mode='screen':all_opacity=1,overlay=x=0:y=0:enable='between(t,{t_in_start},{t_in_end})'{v_in}"
            )

            # 2. B-Roll Content Overlay
            v_br = f"[vbr{i}]"
            filter_complex.append(
                f"{v_in}[br{i}]overlay=x=0:y=0:enable='between(t,{start},{end})'{v_br}"
            )

            # 3. Transition-Out Overlay (Screen Blend)
            t_out_start = end - TRANS_DURATION
            t_out_end = end + TRANS_DURATION
            v_out = f"[vout{i}]"
            filter_complex.append(
                f"{v_br}[tout{i}]blend=all_mode='screen':all_opacity=1,overlay=x=0:y=0:enable='between(t,{t_out_start},{t_out_end})'{v_out}"
            )
            current_v = v_out

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
