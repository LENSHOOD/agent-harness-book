"""Offline, local copy of already installed audit dependencies. Never changes .venv."""
from pathlib import Path
import hashlib
import importlib.metadata
import json
import shutil
import sys

HERE = Path(__file__).resolve().parent
DEST = HERE / "deps"
SOURCES = [
    Path("/Users/xuhai.zhang/.cache/uv/archive-v0/FS0Q5eAV68A5iVxz/lib/python3.13/site-packages"),
    Path("/Users/xuhai.zhang/.cache/uv/archive-v0/5xzzzrt6iZNtHmjF/lib/python3.13/site-packages"),
]
NAMES = ["jsonschema", "jsonschema-specifications", "referencing", "rpds-py", "attrs",
         "typing-extensions", "PyYAML", "pytest", "iniconfig", "packaging", "pluggy", "Pygments"]


def main():
    if (DEST / "dependency_manifest.json").exists():
        # Keep provenance outside ignored deps/ as well.
        manifest = json.loads((DEST / "dependency_manifest.json").read_text())
        for package in manifest:
            for entry in package["files"]:
                local = DEST / entry["path"]
                if not local.is_file() or hashlib.sha256(local.read_bytes()).hexdigest() != entry["sha256"]:
                    raise RuntimeError(f"Local dependency changed/missing: {local}")
        (HERE / "dependency_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print("Using preserved offline dependencies:", DEST)
        return
    DEST.mkdir(exist_ok=True)
    distributions = {}
    for source in SOURCES:
        for dist in importlib.metadata.distributions(path=[str(source)]):
            distributions.setdefault(dist.metadata["Name"].lower().replace("_", "-"), dist)
    manifest = []
    for name in NAMES:
        dist = distributions.get(name.lower())
        if dist is None:
            raise RuntimeError(f"Offline dependency missing: {name}. No network fallback configured.")
        copied = []
        for relative in dist.files or []:
            # Distribution RECORD contains executable scripts outside site-packages;
            # omit them. pytest runs through an apply_patch-created wrapper.
            if ".." in relative.parts or "__pycache__" in relative.parts or relative.suffix == ".pyc":
                continue
            source = Path(dist.locate_file(relative))
            if not source.is_file():
                continue
            destination = DEST / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            copied.append({"path": str(relative), "sha256": hashlib.sha256(source.read_bytes()).hexdigest()})
        manifest.append({"name": name, "version": dist.version, "source": str(dist.locate_file("")), "files": copied})
    (DEST / "dependency_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (HERE / "dependency_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print("Copied cached distributions locally, with hashes:", len(manifest))


if __name__ == "__main__":
    main()
