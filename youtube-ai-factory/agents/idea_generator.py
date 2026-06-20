import argparse
import csv
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.common import IDEA_CSV_FIELDS, ensure_dir  # noqa: E402
from utils.llm import get_default_provider  # noqa: E402


DEFAULT_IDEAS = [
    "Why Data Centers Print Money",
    "How Airports Make Billions",
    "The Hidden Business Behind Parking Lots",
    "Why Subscription Models Win",
    "The Economics of Cloud Computing",
]


def generate_ideas(niche: str, count: int) -> list[dict]:
    provider = get_default_provider()
    prompt = (
        "Generate concise YouTube topic ideas for this niche with a short description and hook. "
        f"Niche: {niche}. Return {count} bullet points."
    )
    response = provider.generate(prompt)
    lines = [line.strip("-• ") for line in response.splitlines() if line.strip()]
    bad_prefixes = ("hook:", "body:", "outro:", "#", "##")
    clean_lines = [line for line in lines if not line.lower().startswith(bad_prefixes)]
    titles = _fill_titles(clean_lines or DEFAULT_IDEAS, count)

    ideas = []
    for i, title in enumerate(titles, start=1):
        ideas.append(
            {
                "id": i,
                "title": title,
                "description": f"A story-driven breakdown of {title.lower()} in business and technology.",
                "hook": f"Most people ignore {title.lower()} until they see the money behind it.",
                "score": max(50, 100 - i),
                "status": "IDEA",
            }
        )
    return ideas


def _fill_titles(seed_titles: list[str], count: int) -> list[str]:
    titles = seed_titles[:count]
    while len(titles) < count:
        titles.append(DEFAULT_IDEAS[len(titles) % len(DEFAULT_IDEAS)])
    return titles


def write_ideas_csv(rows: list[dict], output_path: Path) -> None:
    ensure_dir(output_path.parent)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=IDEA_CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate batch YouTube ideas")
    parser.add_argument("--niche", default="Business, economics, technology")
    parser.add_argument("--count", type=int, default=25)
    parser.add_argument("--output", default="ideas/ideas.csv")
    args = parser.parse_args()

    ideas = generate_ideas(args.niche, args.count)
    write_ideas_csv(ideas, Path(args.output))
    print(f"Generated {len(ideas)} ideas at {args.output}")


if __name__ == "__main__":
    main()
