"""Record the source, dependency checkouts, downloaded inputs, and package hashes."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess


def git(directory, *arguments):
    return subprocess.check_output(
        ["git", "-C", str(directory), *arguments], text=True).strip()


def checksum(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--dependency", type=Path, action="append", default=[])
    parser.add_argument("--downloads", type=Path)
    args = parser.parse_args()

    revision = git(args.source, "rev-parse", "HEAD")
    if os.environ.get("GITHUB_SHA", revision) != revision:
        raise SystemExit("Source checkout does not match the requested workflow commit")

    manifest = {
        "source": {"repository": os.environ.get("GITHUB_REPOSITORY"), "commit": revision},
        "target": args.target,
        "runner": {"os": platform.system(), "architecture": platform.machine()},
        "run_url": (f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
                    f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/"
                    f"{os.environ.get('GITHUB_RUN_ID', '')}"),
        "dependencies": {},
    }
    for path in args.dependency:
        manifest["dependencies"][path.name] = {
            "commit": git(path, "rev-parse", "HEAD"),
        }
    if args.downloads:
        inputs = [p for p in sorted(args.downloads.glob("*.tar.gz"))
                  if not p.name.endswith(".AppImage-debug.tar.gz")]
        inputs.append(args.downloads / "appimagetool")
        manifest["download_sha256"] = {p.name: checksum(p) for p in inputs if p.is_file()}
    manifest["artifact_sha256"] = {
        p.name: checksum(p) for p in sorted(args.output.parent.iterdir())
        if p.is_file() and p != args.output
    }
    args.output.write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
