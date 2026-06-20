import shutil
import subprocess
from pathlib import Path

from utils.common import write_text

SECONDS_PER_IMAGE = 3


class VideoRenderer:
    @staticmethod
    def _format_srt_timestamp(seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d},000"

    def render(self, audio_path: Path, visuals_dir: Path, script: str, output_video_path: Path) -> None:
        images = sorted(visuals_dir.glob("*.png"))
        if not images:
            raise FileNotFoundError(f"No visuals found in {visuals_dir}")

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            error_log = output_video_path.with_suffix(".error.log")
            write_text(error_log, "FFmpeg missing. Install ffmpeg to produce final_video.mp4.")
            output_video_path.write_bytes(b"")
            return

        list_file = output_video_path.parent / "_visuals.txt"
        captions_file = output_video_path.parent / "captions.srt"
        list_file.write_text(
            "\n".join(
                [f"file '{image.resolve()}'\nduration {SECONDS_PER_IMAGE}" for image in images]
                + [f"file '{images[-1].resolve()}'"]
            ),
            encoding="utf-8",
        )
        total_seconds = max(1, len(images) * SECONDS_PER_IMAGE)
        captions_file.write_text(
            f"1\n00:00:00,000 --> {self._format_srt_timestamp(total_seconds)}\n"
            + script.replace("\n", " ")[:120]
            + "\n",
            encoding="utf-8",
        )
        subtitle_path = str(captions_file).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")

        cmd = [
            ffmpeg_path,
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_file),
            "-i",
            str(audio_path),
            "-vf",
            f"subtitles='{subtitle_path}'",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            str(output_video_path),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError:
            fallback_cmd = [
                ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_file),
                "-i",
                str(audio_path),
                "-shortest",
                "-pix_fmt",
                "yuv420p",
                str(output_video_path),
            ]
            subprocess.run(fallback_cmd, check=True, capture_output=True, text=True)
