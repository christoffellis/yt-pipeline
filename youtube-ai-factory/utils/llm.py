import json
import os
import urllib.error
import urllib.request

OLLAMA_TIMEOUT_SECONDS = 120
HEALTHCHECK_TIMEOUT_SECONDS = 2
_DEFAULT_PROVIDER = None


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
        with urllib.request.urlopen(request, timeout=OLLAMA_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        return body.get("response", "").strip()

    def is_available(self) -> bool:
        request = urllib.request.Request(f"{self.host.rstrip('/')}/api/tags", method="GET")
        try:
            with urllib.request.urlopen(request, timeout=HEALTHCHECK_TIMEOUT_SECONDS):
                return True
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
            return False


class FallbackProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        return (
            "Hook: Most people never notice this hidden business machine.\n\n"
            "Body: This industry quietly turns infrastructure into recurring cash flow. "
            "We'll break down who pays, where profits come from, and why it keeps scaling.\n\n"
            "Outro: If you enjoyed this breakdown, comment your next business mystery."
        )



def get_default_provider() -> LLMProvider:
    global _DEFAULT_PROVIDER
    if _DEFAULT_PROVIDER is not None:
        return _DEFAULT_PROVIDER

    try:
        provider = OllamaProvider()
        if provider.is_available():
            _DEFAULT_PROVIDER = provider
            return _DEFAULT_PROVIDER
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        pass

    _DEFAULT_PROVIDER = FallbackProvider()
    return _DEFAULT_PROVIDER
