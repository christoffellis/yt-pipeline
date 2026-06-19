from pathlib import Path

from utils.common import write_text
from utils.llm import get_default_provider


class ScriptAgent:
    def __init__(self):
        self.provider = get_default_provider()

    def generate(self, idea: str, research: str, output_path: Path) -> str:
        prompt = (
            "Write an educational, story-driven YouTube script for 8-12 minutes. "
            "Start with a first-15-second hook and keep natural spoken language. "
            f"Topic: {idea}\nResearch:\n{research}"
        )
        draft = self.provider.generate(prompt)
        script = (
            "# Script\n\n"
            "## Hook (0:00-0:15)\n"
            f"{draft.splitlines()[0] if draft else 'What if this business model runs right under your nose?'}\n\n"
            "## Story\n"
            f"{draft}\n\n"
            "## Closing\n"
            "Thanks for watching. Like and subscribe for more business deep dives.\n"
        )
        write_text(output_path, script)
        return script
