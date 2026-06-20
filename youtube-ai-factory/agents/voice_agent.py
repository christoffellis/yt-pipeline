import math
import wave
from abc import ABC, abstractmethod
from pathlib import Path

from utils.common import ensure_dir

MIN_DURATION_SECONDS = 10
MAX_DURATION_SECONDS = 720
WORDS_PER_SECOND = 2
DEFAULT_SAMPLE_RATE = 16000
DEFAULT_AMPLITUDE = 4000
DEFAULT_FREQUENCY = 220.0


class VoiceProvider(ABC):
    @abstractmethod
    def generate_audio(self, script: str, output_path: Path) -> None:
        raise NotImplementedError


class _BaseWaveProvider(VoiceProvider):
    def __init__(self, model_path: str | None = None):
        self.model_path = model_path

    def generate_audio(self, script: str, output_path: Path) -> None:
        ensure_dir(output_path.parent)
        duration_seconds = max(
            MIN_DURATION_SECONDS,
            min(MAX_DURATION_SECONDS, round(len(script.split()) / WORDS_PER_SECOND)),
        )
        sample_rate = DEFAULT_SAMPLE_RATE
        amplitude = DEFAULT_AMPLITUDE
        frequency = DEFAULT_FREQUENCY
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
