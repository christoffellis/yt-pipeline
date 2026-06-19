import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class PipelineCLITests(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[2]
        self.app_dir = self.repo_root / "youtube-ai-factory"

    def test_pipeline_generates_expected_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cmd = [
                "python",
                str(self.app_dir / "pipeline.py"),
                "--idea",
                "Why Data Centers Print Money",
                "--base-dir",
                temp_dir,
            ]
            run = subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.assertIn("Complete YouTube video package ready for scheduling.", run.stdout)

            project_dir = Path(temp_dir) / "projects" / "why_data_centers_print_money"
            self.assertTrue((project_dir / "research.md").exists())
            self.assertTrue((project_dir / "script.md").exists())
            self.assertTrue((project_dir / "audio.wav").exists())
            self.assertTrue((project_dir / "visual_plan.json").exists())
            self.assertTrue((project_dir / "final_video.mp4").exists())
            self.assertTrue((project_dir / "thumbnail.png").exists())
            self.assertTrue((project_dir / "metadata.json").exists())
            self.assertTrue((project_dir / "state.json").exists())

    def test_pipeline_resume_skips_completed_steps(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_cmd = [
                "python",
                str(self.app_dir / "pipeline.py"),
                "--idea",
                "How Airports Make Billions",
                "--base-dir",
                temp_dir,
            ]
            subprocess.run(base_cmd, check=True, capture_output=True, text=True)

            project_dir = Path(temp_dir) / "projects" / "how_airports_make_billions"
            state_path = project_dir / "state.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            state["steps"]["render"] = False
            state_path.write_text(json.dumps(state), encoding="utf-8")

            second = subprocess.run(base_cmd, check=True, capture_output=True, text=True)
            self.assertIn("Rendering video...", second.stdout)
            self.assertNotIn("Running research agent...", second.stdout)


if __name__ == "__main__":
    unittest.main()
