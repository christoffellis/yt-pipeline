import shutil
import subprocess
from pathlib import Path

from utils.common import write_text


class VideoRenderer:
    def render(self, audio_path: Path, visuals_dir: Path, script: str, output_video_path: Path) -> None:
        images = sorted(visuals_dir.glob("*.png"))
        if not images:
            raise FileNotFoundError(f"No visuals found in {visuals_dir}")

        ffmpeg_path = shutil.which("ffmpeg")
        if not ffmpeg_path:
            write_text(output_video_path, "FFmpeg missing. Install ffmpeg to produce a playable MP4.")
            return

        list_file = output_video_path.parent / "_visuals.txt"
        captions_file = output_video_path.parent / "captions.srt"
        list_file.write_text(
            "\n".join([f"file '{image.resolve()}'\nduration 3" for image in images] + [f"file '{images[-1].resolve()}'"]),
            encoding="utf-8",
        )
        captions_file.write_text(
            "1\n00:00:00,000 --> 00:00:10,000\n"
            + script.replace("\n", " ")[:120]
            + "\n",
            encoding="utf-8",
        )

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
            f"subtitles={captions_file}",
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
