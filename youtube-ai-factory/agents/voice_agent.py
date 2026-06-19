import math
import wave
from abc import ABC, abstractmethod
from pathlib import Path

from utils.common import ensure_dir


class VoiceProvider(ABC):
    @abstractmethod
    def generate_audio(self, script: str, output_path: Path) -> None:
        raise NotImplementedError


class _BaseWaveProvider(VoiceProvider):
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path

    def generate_audio(self, script: str, output_path: Path) -> None:
        ensure_dir(output_path.parent)
        duration_seconds = max(10, min(720, len(script.split()) // 2))
        sample_rate = 16000
        amplitude = 4000
        frequency = 220.0
        n_frames = duration_seconds * sample_rate

        with wave.open(str(output_path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            for i in range(n_frames):
                value = int(amplitude * math.sin(2 * math.pi * frequency * i / sample_rate))
                wav.writeframesraw(value.to_bytes(2, byteorder="little", signed=True))


class XTTSVoiceProvider(_BaseWaveProvider):
    pass


class CoquiVoiceProvider(_BaseWaveProvider):
    pass


def get_voice_provider(name: str, model_path: str | None = None) -> VoiceProvider:
    provider = (name or "xtts").strip().lower()
    if provider == "coqui":
        return CoquiVoiceProvider(model_path=model_path)
    return XTTSVoiceProvider(model_path=model_path)
