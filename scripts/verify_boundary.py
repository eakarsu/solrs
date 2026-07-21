#!/usr/bin/env python3
"""Verify the immutable upstream-library boundary without executing the JVM graph."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


class BoundaryError(RuntimeError):
    pass


ALLOWED_NEW = {
    ".github/workflows/boundary.yml",
    "BOUNDARY.json",
    "OPERATIONS.md",
    "SECURITY.md",
    "_COMPLETENESS_REVIEW.md",
    "scripts/verify-boundary.sh",
    "scripts/verify_boundary.py",
    "start.sh",
    "tests/test_boundary.py",
}
REQUIRED_UNRESOLVED = {
    "accountable-owner", "supported-version", "update-cadence",
    "security-patching-owner", "dependency-review", "isolated-build-evidence",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise BoundaryError(message)


def git(root: Path, *args: str, binary: bool = False):
    result = subprocess.run(["git", *args], cwd=root, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout if binary else result.stdout.decode("utf-8", "strict").strip()


def validate_boundary(data: dict) -> None:
    require(data.get("schemaVersion") == 2, "unsupported boundary schema")
    require(data.get("artifactType") == "upstream-scala-library", "wrong artifact type")
    require(data.get("disposition") == "retain-immutable-upstream-reference", "unsafe disposition")
    require(data.get("deployableApplication") is False, "reference cannot become an application")
    require(data.get("runtimeAcceptance") == "not_applicable", "runtime must remain not applicable")
    require(data.get("loginAcceptance") == "not_applicable", "login must remain not applicable")
    require(data.get("license") == "Apache-2.0", "license classification changed")
    require(REQUIRED_UNRESOLVED.issubset(data.get("unresolved", [])), "unresolved adoption gate removed")
    require({"publish-snapshot", "use-legacy-release-key", "connect-shared-solr"}.issubset(data.get("prohibitedOperations", [])), "release/network prohibition weakened")


def tree_entries(root: Path, commit: str):
    raw = git(root, "ls-tree", "-r", "-z", "-l", commit, binary=True)
    entries = []
    for row in raw.split(b"\0"):
        if not row:
            continue
        metadata, encoded_path = row.split(b"\t", 1)
        mode, object_type, object_id, size = metadata.decode("ascii").split()
        entries.append((encoded_path.decode("utf-8", "surrogateescape"), mode, object_type, object_id, int(size)))
    return entries


def verify(root: Path) -> dict[str, int]:
    root = root.resolve()
    data = json.loads((root / "BOUNDARY.json").read_text(encoding="utf-8"))
    validate_boundary(data)
    snapshot = data["snapshot"]
    require(Path(git(root, "rev-parse", "--show-toplevel")).resolve() == root, "wrong repository root")
    require(git(root, "rev-parse", f"{snapshot['commit']}^{{tree}}") == snapshot["tree"], "snapshot tree mismatch")
    require(int(git(root, "rev-list", "--count", snapshot["commit"])) == snapshot["commits"], "snapshot commit count mismatch")
    entries = tree_entries(root, snapshot["commit"])
    require(len(entries) == snapshot["trackedFiles"], "snapshot file count mismatch")
    require(sum(row[4] for row in entries) == snapshot["trackedBytes"], "snapshot byte count mismatch")
    retained_link = data["retainedSymlink"]
    for relative, mode, object_type, object_id, _size in entries:
        if mode == "120000" and relative == retained_link["path"]:
            path = root / relative
            require(path.is_symlink(), f"retained fixture link missing: {relative}")
            require(os.readlink(path) == retained_link["target"], f"retained fixture link target changed: {relative}")
            require(path.resolve().is_relative_to(root), f"retained fixture link escapes repository: {relative}")
            continue
        require(mode == "100644" and object_type == "blob", f"unsupported snapshot object: {relative}")
        path = root / relative
        require(path.is_file() and not path.is_symlink(), f"snapshot file missing or non-regular: {relative}")
        require(git(root, "hash-object", "--", relative) == object_id, f"upstream payload changed: {relative}")
    require(not git(root, "diff", "--name-only", snapshot["commit"], "--"), "tracked upstream payload has drifted")
    untracked = {
        row.decode("utf-8", "surrogateescape")
        for row in git(root, "ls-files", "--others", "--exclude-standard", "-z", binary=True).split(b"\0") if row
    }
    require(untracked <= ALLOWED_NEW, f"unexpected untracked material: {sorted(untracked - ALLOWED_NEW)}")

    for path in root.rglob("*"):
        if ".git" in path.relative_to(root).parts:
            continue
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            require(relative == retained_link["path"] and os.readlink(path) == retained_link["target"], f"unexpected symlink: {relative}")
    license_body = (root / "LICENSE.txt").read_bytes()
    require(hashlib.sha256(license_body).hexdigest() == data["licenseSha256"], "license file changed")
    legacy = data["legacyReleaseMaterial"]
    legacy_path = root / legacy["path"]
    require(legacy_path.stat().st_size == legacy["bytes"], "legacy release artifact size changed")
    require(hashlib.sha256(legacy_path.read_bytes()).hexdigest() == legacy["sha256"], "legacy release artifact changed")
    require(legacy["useAllowed"] is False, "legacy release material cannot be enabled")

    build = (root / "build.sbt").read_text(encoding="utf-8")
    properties = (root / "project/build.properties").read_text(encoding="utf-8")
    version = (root / "version.sbt").read_text(encoding="utf-8")
    for evidence in ['scalaVersion := "2.12.8"', '"2.13.1"', 'val solrVersion = "7.7.2"', 'java.specification.version', 'publishTo in ThisBuild']:
        require(evidence in build, f"archived build evidence missing: {evidence}")
    require("sbt.version=1.3.3" in properties, "archived sbt version changed")
    require('version := "2.4.2-SNAPSHOT"' in version, "snapshot version changed")
    review = (root / "_COMPLETENESS_REVIEW.md").read_text(encoding="utf-8")
    require(review.count("## Implementation progress (2026-07-20)") == 1, "implementation heading must occur exactly once")
    return {"files": len(entries), "bytes": sum(row[4] for row in entries), "commits": snapshot["commits"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        result = verify(args.root)
    except (BoundaryError, KeyError, OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as error:
        print(f"solrs boundary verification failed: {error}", file=sys.stderr)
        return 1
    print(f"solrs upstream snapshot verified: {result['files']} files/{result['bytes']} bytes/{result['commits']} commits; runtime and login are not applicable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
