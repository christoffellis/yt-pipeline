import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agents.visual_agent import VisualAgent

MIN_PROCEDURAL_IMAGE_SIZE_BYTES = 1024


class VisualAgentProviderTests(unittest.TestCase):
    def test_picsum_provider_writes_api_image_bytes(self):
        scene = {
            "scene": 1,
            "prompt": "cinematic wide shot",
            "image_file": "001.png",
        }
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(os.environ, {"IMAGE_PROVIDER": "picsum"}):
            visuals_dir = Path(temp_dir)
            api_bytes = b"fake-jpeg-image-bytes"

            response = mock.MagicMock()
            response.read.return_value = api_bytes
            response.__enter__.return_value = response

            with mock.patch("agents.visual_agent.urllib.request.urlopen", return_value=response):
                VisualAgent()._generate_image(scene, visuals_dir)

            self.assertEqual((visuals_dir / "001.png").read_bytes(), api_bytes)

    def test_picsum_provider_falls_back_to_procedural_image(self):
        scene = {
            "scene": 2,
            "prompt": "editorial close-up",
            "image_file": "002.png",
        }
        with tempfile.TemporaryDirectory() as temp_dir, mock.patch.dict(os.environ, {"IMAGE_PROVIDER": "picsum"}):
            visuals_dir = Path(temp_dir)

            with mock.patch(
                "agents.visual_agent.urllib.request.urlopen",
                side_effect=urllib.error.URLError("network down"),
            ):
                VisualAgent()._generate_image(scene, visuals_dir)

            self.assertGreater((visuals_dir / "002.png").stat().st_size, MIN_PROCEDURAL_IMAGE_SIZE_BYTES)


if __name__ == "__main__":
    unittest.main()
