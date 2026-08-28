from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANUSCRIPT = ROOT / "manuscript"
STRUCTURE_PATH = ROOT / "publishing" / "book_structure.json"


def fail(message: str) -> None:
    raise SystemExit(f"BOOK STRUCTURE AUDIT: FAIL — {message}")


def main() -> None:
    structure = json.loads(STRUCTURE_PATH.read_text())
    chapters = [chapter for part in structure["parts"] for chapter in part["chapters"]]
    numbers = [chapter["number"] for chapter in chapters]
    slugs = [chapter["slug"] for chapter in chapters]

    if numbers != list(range(1, 31)):
        fail(f"chapter numbers are not exactly 1..30: {numbers}")
    if len(slugs) != len(set(slugs)):
        fail("chapter slugs are not unique")

    preface = structure["preface"]
    preface_path = MANUSCRIPT / "chapters" / f"{preface['slug']}.md"
    if not preface_path.is_file() or preface_path.read_text().splitlines()[0] != f"# {preface['title']}":
        fail(f"preface title drift: {preface_path}")

    for part in structure["parts"]:
        intro = MANUSCRIPT / "parts" / f"{part['intro']}.md"
        if not intro.is_file():
            fail(f"missing part introduction: {intro}")
        for chapter in part["chapters"]:
            path = MANUSCRIPT / "chapters" / f"{chapter['slug']}.md"
            if not path.is_file():
                fail(f"missing chapter: {path}")
            first_line = path.read_text().splitlines()[0]
            if first_line != f"# {chapter['title']}":
                fail(f"title drift in {path.name}: {first_line!r} != {chapter['title']!r}")

    print(f"BOOK STRUCTURE AUDIT: PASS — {len(chapters)} canonical chapter titles")


if __name__ == "__main__":
    main()
