import json
import os
import urllib.error
import urllib.request


class LLMProvider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError


class OllamaProvider(LLMProvider):
    def __init__(self, model: str | None = None, host: str | None = None):
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")

    def generate(self, prompt: str) -> str:
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.host.rstrip('/')}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body.get("response", "").strip()


class FallbackProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return (
            "Hook: Most people never notice this hidden business machine.\n\n"
            "Body: This industry quietly turns infrastructure into recurring cash flow. "
            "We'll break down who pays, where profits come from, and why it keeps scaling.\n\n"
            "Outro: If you enjoyed this breakdown, comment your next business mystery."
        )



def get_default_provider() -> LLMProvider:
    try:
        provider = OllamaProvider()
        provider.generate("Respond with one word: ready")
        return provider
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        return FallbackProvider()
