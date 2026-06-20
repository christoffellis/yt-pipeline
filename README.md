# yt-pipeline

Local Python automation for building an AI-powered YouTube content production package.

## Project layout

```text
youtube-ai-factory/
├── pipeline.py
├── ideas/
│   └── ideas.csv
├── projects/
├── agents/
│   ├── idea_generator.py
│   ├── research_agent.py
│   ├── script_agent.py
│   ├── voice_agent.py
│   ├── visual_agent.py
│   ├── video_renderer.py
│   ├── thumbnail_agent.py
│   └── youtube_uploader.py
├── integrations/
│   ├── google_sheets.py
│   └── youtube.py
├── config/
│   └── settings.yaml
├── utils/
└── tests/
```

## 1) Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install google-api-python-client google-auth
```

Also install:

- `ffmpeg`
- `ollama`
- XTTS / Coqui TTS runtime for your preferred voice workflow
- Stable Diffusion / FLUX runtime if you replace placeholder image generation

## 2) Setup Ollama

```bash
ollama pull qwen2.5:7b
ollama serve
```

Set `OLLAMA_MODEL` in `.env` if you use a different model.

## 3) Setup voice cloning (XTTS / Coqui)

- Train or prepare your speaker model/checkpoint using XTTS or Coqui tooling.
- Put the model path in `VOICE_MODEL_PATH`.
- Current implementation exposes a `VoiceProvider` abstraction (`agents/voice_agent.py`) so you can swap in your actual XTTS/Coqui inference call.

## 4) Setup image generation

- Set `IMAGE_PROVIDER=procedural` (default) for deterministic local scene generation.
- Put your image model path in `IMAGE_MODEL_PATH`.
- `agents/visual_agent.py` now creates a structured per-scene visual plan (style/shot/motion/prompt)
  and renders deterministic scene PNGs locally.
- To integrate Stable Diffusion / FLUX, extend the provider branch in `VisualAgent._generate_image`.

## 5) Setup Google Sheets API

- Create a Google Cloud service account.
- Share your target sheet with the service account email.
- Save credentials JSON locally and set `GOOGLE_SERVICE_ACCOUNT_JSON`.
- Set `GOOGLE_SHEET_ID`.

If not configured, tracking falls back to `projects/tracking.csv`.

## 6) Run idea generator (batch mode)

```bash
cd youtube-ai-factory
python agents/idea_generator.py --niche "Business, economics, technology" --count 25 --output ideas/ideas.csv
```

## 7) Run production pipeline

```bash
cd youtube-ai-factory
python pipeline.py --idea "Why Data Centers Print Money"
```

Artifacts are created in `youtube-ai-factory/projects/<slug>/`:

- `research.md`
- `script.md`
- `audio.wav`
- `visual_plan.json`
- `visuals/*.png`
- `final_video.mp4`
- `thumbnail.png`
- `metadata.json`

The pipeline is resumable and skips completed steps via `state.json`.

## 8) Generate videos in batches

1. Generate many ideas into `ideas/ideas.csv`.
2. Pick an idea title.
3. Run `pipeline.py --idea "..."` for each selected idea.
4. Manually review assets.
5. Optional upload:

```bash
python pipeline.py --upload <project_folder_slug>
```

## Development checks

```bash
python -m unittest discover -s youtube-ai-factory/tests -q
```
