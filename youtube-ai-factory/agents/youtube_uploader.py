import json
from pathlib import Path

from integrations.youtube import YouTubeUploader


class ProjectUploader:
    def __init__(self):
        self.uploader = YouTubeUploader()

    def upload_project(self, project_dir: Path) -> str | None:
        metadata_path = project_dir / "metadata.json"
        if not metadata_path.exists():
            return None

        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        video_path = project_dir / "final_video.mp4"
        thumbnail_path = project_dir / "thumbnail.png"
        if not video_path.exists():
            return None

        return self.uploader.upload(
            video_path=video_path,
            title=metadata.get("title_options", [project_dir.name])[0],
            description=metadata.get("description", ""),
            tags=metadata.get("tags", []),
            thumbnail_path=thumbnail_path if thumbnail_path.exists() else None,
        )
