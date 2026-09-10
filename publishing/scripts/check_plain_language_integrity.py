#!/usr/bin/env python3
"""Check that prose rewrites preserve machine-sensitive manuscript content."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess
import sys


HEADING_RE = re.compile(r"^#{1,6} .+$", re.MULTILINE)
URL_RE = re.compile(r"https?://[^)\s>]+")
FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
NUMBER_RE = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*(?:%|年|月|日|个|次|名|题|倍)?")
SENTENCE_SPLIT_RE = re.compile(r"[。！？；\n]+")


def git_show(revision: str, path: str) -> str:
    return subprocess.check_output(
        ["git", "show", f"{revision}:{path}"], text=True
    )


def chinese_char_count(text: str) -> int:
    return sum(0x3400 <= ord(char) <= 0x9FFF for char in text)


def long_sentence_count(text: str, threshold: int = 120) -> int:
    prose = FENCE_RE.sub("", text)
    prose = "\n".join(
        line
        for line in prose.splitlines()
        if not line.startswith(("#", "|"))
        and not re.fullmatch(r"(?:\[[^]]+\]\([^)]+\)[、，,。]?)+", line.strip())
    )
    return sum(
        len(sentence.strip()) > threshold
        for sentence in SENTENCE_SPLIT_RE.split(prose)
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD")
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()

    failed = False
    for path in args.paths:
        old = git_show(args.base, path)
        new = pathlib.Path(path).read_text()
        old_count = chinese_char_count(old)
        new_count = chinese_char_count(new)
        ratio = new_count / old_count if old_count else 1.0
        checks = {
            "headings_exact": HEADING_RE.findall(old) == HEADING_RE.findall(new),
            "urls_exact": URL_RE.findall(old) == URL_RE.findall(new),
            "code_blocks_exact": FENCE_RE.findall(old) == FENCE_RE.findall(new),
            "numbers_exact": NUMBER_RE.findall(old) == NUMBER_RE.findall(new),
            "length_in_range": 0.95 <= ratio <= 1.20,
        }
        passed = all(checks.values())
        failed |= not passed
        print(
            json.dumps(
                {
                    "file": path,
                    "chinese_chars_before": old_count,
                    "chinese_chars_after": new_count,
                    "ratio": round(ratio, 3),
                    "long_sentences_before": long_sentence_count(old),
                    "long_sentences_after": long_sentence_count(new),
                    "passed": passed,
                    **checks,
                },
                ensure_ascii=False,
            )
        )

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
