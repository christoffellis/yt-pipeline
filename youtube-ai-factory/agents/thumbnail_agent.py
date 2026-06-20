from pathlib import Path

from utils.common import write_json, write_placeholder_png


class ThumbnailAgent:
    def generate(self, idea: str, thumbnail_path: Path, metadata_path: Path) -> dict:
        write_placeholder_png(thumbnail_path)

        metadata = {
            "title_options": [
                idea,
                f"{idea} (Explained)",
                f"The Economics of {idea}",
            ],
            "description": (
                f"In this video, we break down {idea.lower()} with practical examples and a story-driven flow."
            ),
            "tags": ["business", "economics", "technology", "explained"],
        }
        write_json(metadata_path, metadata)
        return metadata
