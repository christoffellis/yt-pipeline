import argparse
from pathlib import Path

from agents.research_agent import ResearchAgent
from agents.script_agent import ScriptAgent
from agents.thumbnail_agent import ThumbnailAgent
from agents.video_renderer import VideoRenderer
from agents.visual_agent import VisualAgent
from agents.voice_agent import get_voice_provider
from agents.youtube_uploader import ProjectUploader
from integrations.google_sheets import GoogleSheetsTracker
from utils.common import ensure_dir, read_json, read_text, slugify, utc_now_iso, write_json
from utils.logging_utils import log

STATUS = {
    "research": "RESEARCHED",
    "script": "SCRIPT_READY",
    "voice": "VOICE_READY",
    "visuals": "VISUALS_READY",
    "render": "RENDERED",
    "thumbnail": "READY_FOR_REVIEW",
    "uploaded": "UPLOADED",
}


def _default_state(idea: str, project_dir: Path) -> dict:
    return {
        "id": project_dir.name,
        "idea": idea,
        "status": "IDEA",
        "created_date": utc_now_iso(),
        "steps": {
            "research": False,
            "script": False,
            "voice": False,
            "visuals": False,
            "render": False,
            "thumbnail": False,
            "uploaded": False,
        },
        "youtube_link": "",
    }


def _row_from_state(state: dict, metadata: dict, project_dir: Path) -> dict:
    return {
        "ID": state["id"],
        "Status": state["status"],
        "Title": metadata.get("title_options", [state["idea"]])[0],
        "Description": metadata.get("description", ""),
        "Project Folder": str(project_dir),
        "Script Complete": state["steps"]["script"],
        "Audio Complete": state["steps"]["voice"],
        "Visuals Complete": state["steps"]["visuals"],
        "Video Complete": state["steps"]["render"],
        "Thumbnail Complete": state["steps"]["thumbnail"],
        "YouTube Link": state.get("youtube_link", ""),
        "Created Date": state.get("created_date", ""),
        "Published Date": state.get("published_date", ""),
        "Notes": state.get("notes", ""),
    }


def run_pipeline(idea: str, base_dir: Path, project_root: str = "projects") -> Path:
    slug = slugify(idea)
    project_dir = ensure_dir(base_dir / project_root / slug)
    visuals_dir = ensure_dir(project_dir / "visuals")

    research_file = project_dir / "research.md"
    script_file = project_dir / "script.md"
    audio_file = project_dir / "audio.wav"
    visual_plan_file = project_dir / "visual_plan.json"
    final_video_file = project_dir / "final_video.mp4"
    thumbnail_file = project_dir / "thumbnail.png"
    metadata_file = project_dir / "metadata.json"
    state_file = project_dir / "state.json"

    state = read_json(state_file, _default_state(idea, project_dir))

    tracker = GoogleSheetsTracker(local_fallback=base_dir / project_root / "tracking.csv")

    if not state["steps"]["research"]:
        log("Running research agent...")
        ResearchAgent().generate(idea, research_file)
        state["steps"]["research"] = True
        state["status"] = STATUS["research"]
        write_json(state_file, state)

    if not state["steps"]["script"]:
        log("Generating script...")
        research = read_text(research_file)
        ScriptAgent().generate(idea, research, script_file)
        state["steps"]["script"] = True
        state["status"] = STATUS["script"]
        write_json(state_file, state)

    if not state["steps"]["voice"]:
        log("Generating voice...")
        script = read_text(script_file)
        provider = get_voice_provider(name="xtts")
        provider.generate_audio(script, audio_file)
        state["steps"]["voice"] = True
        state["status"] = STATUS["voice"]
        write_json(state_file, state)

    if not state["steps"]["visuals"]:
        log("Generating visuals...")
        script = read_text(script_file)
        VisualAgent().generate(script, visual_plan_file, visuals_dir)
        state["steps"]["visuals"] = True
        state["status"] = STATUS["visuals"]
        write_json(state_file, state)

    if not state["steps"]["render"]:
        log("Rendering video...")
        script = read_text(script_file)
        VideoRenderer().render(audio_file, visuals_dir, script, final_video_file)
        state["steps"]["render"] = True
        state["status"] = STATUS["render"]
        write_json(state_file, state)

    metadata = read_json(metadata_file, {})
    if not state["steps"]["thumbnail"]:
        log("Generating thumbnail + metadata...")
        metadata = ThumbnailAgent().generate(idea, thumbnail_file, metadata_file)
        state["steps"]["thumbnail"] = True
        state["status"] = STATUS["thumbnail"]
        write_json(state_file, state)

    tracker.upsert_row(_row_from_state(state, metadata, project_dir))

    log("Pipeline finished.")
    print("Complete YouTube video package ready for scheduling.")
    return project_dir


def run_upload(project_name: str, base_dir: Path, project_root: str = "projects") -> None:
    project_dir = base_dir / project_root / project_name
    if not project_dir.exists():
        raise FileNotFoundError(f"Project not found: {project_dir}")

    state_file = project_dir / "state.json"
    metadata = read_json(project_dir / "metadata.json", {})
    state = read_json(state_file, _default_state(project_name, project_dir))

    link = ProjectUploader().upload_project(project_dir)
    if link:
        state["steps"]["uploaded"] = True
        state["status"] = STATUS["uploaded"]
        state["youtube_link"] = link
        state["published_date"] = utc_now_iso()
        write_json(state_file, state)

    tracker = GoogleSheetsTracker(local_fallback=base_dir / project_root / "tracking.csv")
    tracker.upsert_row(_row_from_state(state, metadata, project_dir))


def main() -> None:
    parser = argparse.ArgumentParser(description="Local AI YouTube content pipeline")
    parser.add_argument("--idea", help="Idea title to produce")
    parser.add_argument("--upload", help="Existing project folder name to upload")
    parser.add_argument("--project-root", default="projects")
    parser.add_argument("--base-dir", default=str(Path(__file__).resolve().parent))
    args = parser.parse_args()

    base_dir = Path(args.base_dir).resolve()

    if args.upload:
        run_upload(args.upload, base_dir, project_root=args.project_root)
        return

    if not args.idea:
        parser.error("Provide --idea or --upload")

    run_pipeline(args.idea, base_dir, project_root=args.project_root)


if __name__ == "__main__":
    main()
