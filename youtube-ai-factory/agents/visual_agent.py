from pathlib import Path

from utils.common import write_json, write_placeholder_png


class VisualAgent:
    def generate(self, script: str, visual_plan_path: Path, visuals_dir: Path) -> list[dict]:
        lines = [line.strip() for line in script.splitlines() if line.strip()]
        story_lines = [line for line in lines if not line.startswith("#")][:8]
        if not story_lines:
            story_lines = ["Opening context", "Core concept", "Final takeaway"]

        plan = [
            {
                "scene": index + 1,
                "description": text[:120],
                "type": "image",
            }
            for index, text in enumerate(story_lines)
        ]
        write_json(visual_plan_path, plan)

        for scene in plan:
            filename = visuals_dir / f"{scene['scene']:03d}.png"
            write_placeholder_png(filename)

        return plan
