import base64
import json
import re
from datetime import datetime, timezone
from pathlib import Path

MINIMAL_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO7d6v8AAAAASUVORK5CYII="
)
IDEA_CSV_FIELDS = ["id", "title", "description", "hook", "score", "status"]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", value.strip().lower()).strip("_")
    return slug or "untitled_video"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")


def read_text(path: Path, default: str = "") -> str:
    if not path.exists():
        return default
    return path.read_text(encoding="utf-8")


def write_json(path: Path, payload: dict | list) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def read_json(path: Path, default: dict | list | None) -> dict | list | None:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_placeholder_png(path: Path) -> None:
    ensure_dir(path.parent)
    path.write_bytes(base64.b64decode(MINIMAL_PNG_BASE64))
