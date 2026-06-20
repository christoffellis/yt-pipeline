import hashlib
import os
import random
import struct
import urllib.error
import urllib.request
import zlib
from pathlib import Path

from utils.common import write_json
from utils.logging_utils import log

MAX_STORY_SCENES = 8
DEFAULT_SCENE_SIZE = (640, 360)
MAX_BEAT_LENGTH = 220
MAX_DESCRIPTION_LENGTH = 120
SCENE_STYLES = ("cinematic", "editorial", "documentary", "isometric", "infographic")
SHOT_TYPES = ("wide shot", "medium shot", "close-up", "aerial perspective")
CAMERA_MOTION = ("slow zoom in", "dolly forward", "pan left to right", "locked framing")
SUPPORTED_IMAGE_PROVIDERS = ("procedural", "picsum")
CHANNEL_BASE_MIN = 24
CHANNEL_BASE_MAX = 128
X_MULTIPLIER_MIN = 3
X_MULTIPLIER_MAX = 17
Y_MULTIPLIER_MIN = 5
Y_MULTIPLIER_MAX = 19
WAVE_MULTIPLIER_MIN = 11
WAVE_MULTIPLIER_MAX = 29
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Return one PNG chunk encoded as length + type + data + CRC32."""
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", zlib.crc32(chunk_type + data) & 0xFFFFFFFF)


def _write_scene_png(path: Path, seed_text: str, size: tuple[int, int] = DEFAULT_SCENE_SIZE) -> None:
    """Render a deterministic abstract RGB PNG for a scene from prompt-derived seed text."""
    width, height = size
    seed = int(hashlib.sha256(seed_text.encode("utf-8")).hexdigest()[:16], 16)
    rng = random.Random(seed)

    red_base = rng.randint(CHANNEL_BASE_MIN, CHANNEL_BASE_MAX)
    green_base = rng.randint(CHANNEL_BASE_MIN, CHANNEL_BASE_MAX)
    blue_base = rng.randint(CHANNEL_BASE_MIN, CHANNEL_BASE_MAX)
    x_mul = rng.randint(X_MULTIPLIER_MIN, X_MULTIPLIER_MAX)
    y_mul = rng.randint(Y_MULTIPLIER_MIN, Y_MULTIPLIER_MAX)
    wave_mul = rng.randint(WAVE_MULTIPLIER_MIN, WAVE_MULTIPLIER_MAX)

    scanlines = bytearray()
    for y in range(height):
        scanlines.append(0)
        for x in range(width):
            wave = (x * y * wave_mul + seed) & 0xFF
            r = (red_base + x * x_mul + y * (y_mul // 2) + wave) & 0xFF
            g = (green_base + x * (y_mul // 2) + y * y_mul + (wave // 2)) & 0xFF
            b = (blue_base + (x + y) * (x_mul // 2) + (wave // 3)) & 0xFF
            scanlines.extend((r, g, b))

    png_data = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            _png_chunk(b"IDAT", zlib.compress(bytes(scanlines), level=9)),
            _png_chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png_data)


class VisualAgent:
    def __init__(self) -> None:
        provider = os.getenv("IMAGE_PROVIDER", "procedural").strip().lower()
        self.image_provider = provider or "procedural"
        self.image_timeout_seconds = int(os.getenv("IMAGE_API_TIMEOUT_SECONDS", "20"))

    def _build_scene(self, scene_number: int, text: str) -> dict:
        """Build scene metadata and generation prompts for a single script beat."""
        style = SCENE_STYLES[(scene_number - 1) % len(SCENE_STYLES)]
        shot = SHOT_TYPES[(scene_number - 1) % len(SHOT_TYPES)]
        motion = CAMERA_MOTION[(scene_number - 1) % len(CAMERA_MOTION)]
        beat = text[:MAX_BEAT_LENGTH]
        prompt = (
            f"{style} YouTube explainer frame, {shot}, {motion}, "
            f"clean composition, high detail, visualizing: {beat}"
        )
        return {
            "scene": scene_number,
            "type": "image",
            "description": beat[:MAX_DESCRIPTION_LENGTH],
            "beat": beat,
            "style": style,
            "shot_type": shot,
            "camera_motion": motion,
            "prompt": prompt,
            "negative_prompt": "blurry, low quality, watermark, logo, text overlays",
            "duration_seconds": 3,
            "image_file": f"{scene_number:03d}.png",
        }

    def _generate_image(self, scene: dict, visuals_dir: Path) -> None:
        """Dispatch image generation to the configured provider for this scene."""
        filename = visuals_dir / scene["image_file"]
        if self.image_provider == "procedural":
            _write_scene_png(filename, f"{scene['scene']}::{scene['prompt']}")
            return
        if self.image_provider == "picsum":
            seed = hashlib.sha256(scene["prompt"].encode("utf-8")).hexdigest()[:16]
            width, height = DEFAULT_SCENE_SIZE
            url = f"https://picsum.photos/seed/{seed}/{width}/{height}.png"
            log(f"Fetching scene {scene['scene']} image from Picsum")
            try:
                with urllib.request.urlopen(url, timeout=self.image_timeout_seconds) as response:
                    data = response.read()
                    if not data:
                        raise ValueError("Picsum returned empty response")
                    if not data.startswith(PNG_SIGNATURE):
                        raise ValueError("Picsum returned non-PNG image data")
                    filename.write_bytes(data)
                    return
            except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as exc:
                log(f"Picsum image fetch failed for scene {scene['scene']} ({type(exc).__name__}): {exc}")
                _write_scene_png(filename, f"{scene['scene']}::{scene['prompt']}")
                return
        raise ValueError(
            f"Unsupported IMAGE_PROVIDER='{self.image_provider}'. Supported: {', '.join(SUPPORTED_IMAGE_PROVIDERS)}"
        )

    def generate(self, script: str, visual_plan_path: Path, visuals_dir: Path) -> list[dict]:
        lines = [line.strip() for line in script.splitlines() if line.strip()]
        story_lines = [line for line in lines if not line.startswith("#")][:MAX_STORY_SCENES]
        if not story_lines:
            story_lines = ["Opening context", "Core concept", "Final takeaway"]

        plan = [self._build_scene(index + 1, text) for index, text in enumerate(story_lines)]
        write_json(visual_plan_path, plan)

        visuals_dir.mkdir(parents=True, exist_ok=True)
        for scene in plan:
            self._generate_image(scene, visuals_dir)

        return plan
