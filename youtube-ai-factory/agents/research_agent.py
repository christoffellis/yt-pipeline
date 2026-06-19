from pathlib import Path

from utils.common import write_text
from utils.llm import get_default_provider


class ResearchAgent:
    def __init__(self):
        self.provider = get_default_provider()

    def generate(self, idea: str, output_path: Path) -> str:
        prompt = (
            "Create concise YouTube research notes for this topic. Include key facts, "
            "angles, and credibility checks. Topic: "
            f"{idea}"
        )
        draft = self.provider.generate(prompt)
        research = f"# Research\n\n## Topic\n{idea}\n\n## Notes\n{draft}\n"
        write_text(output_path, research)
        return research
