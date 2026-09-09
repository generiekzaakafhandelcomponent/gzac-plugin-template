#!/usr/bin/env python3
"""Rename the gzac-plugin-template scaffold into a real GZAC plugin.

Does the whole mechanical rename in one pass: directory/file names, Kotlin
packages and class names, Angular library/component/selector names, plugin and
action keys, Gradle/npm coordinates, docker db names and docs.

    python3 rename_template.py --artifact brp-plugin --project brp-plugin --version 0.1.0

Nothing about the target API is touched -- the client, actions and frontend
forms are rewritten from the OpenAPI spec afterwards.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git",
    ".gradle",
    ".idea",
    ".kotlin",
    ".angular",
    "node_modules",
    "build",
    "dist",
    "deployment",
    "out",
    # Skills and agent definitions document the template's own names on purpose;
    # rewriting them would destroy this script's own reference material.
    ".claude",
}
BINARY_SUFFIXES = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".jar", ".zip", ".woff", ".woff2",
    ".ttf", ".eot", ".pdf", ".class", ".keystore",
}
# The logo constant's value is base64 -- never substitute inside it.
BASE64_MARKER = ";base64,"

KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(-[0-9A-Za-z.-]+)?$")


class Names:
    def __init__(self, artifact: str, project: str, title: str | None):
        self.artifact = artifact
        self.project = project
        # `sample-plugin` -> base `sample`, mirroring the template's own naming.
        self.base = artifact[: -len("-plugin")] if artifact.endswith("-plugin") else artifact
        tokens = self.base.split("-")
        self.pascal = "".join(t[:1].upper() + t[1:] for t in tokens)
        self.camel = tokens[0] + "".join(t[:1].upper() + t[1:] for t in tokens[1:])
        self.package = artifact.replace("-", "")
        self.upper_snake = artifact.upper().replace("-", "_")
        self.title = title or (" ".join(t.capitalize() for t in tokens) + " Plugin")
        self.project_title = " ".join(t.capitalize() for t in project.split("-"))

    def replacements(self) -> list[tuple[re.Pattern[str], str]]:
        """Ordered longest-match-first; each pattern's input is gone by the next."""
        return [
            (re.compile(r"SAMPLE_PLUGIN"), self.upper_snake),
            (re.compile(r"Sample Plugin"), self.title),
            (re.compile(r"GZAC Plugin Template"), self.project_title),
            (re.compile(r"GZAC plugin-template"), self.project),
            (re.compile(r"gzac-plugin-template"), self.project),
            (re.compile(r"sample-plugin"), self.artifact),
            (re.compile(r"sampleplugin"), self.package),
            (re.compile(r"Sample"), self.pascal),
            # camelCase identifiers (sampleClient) vs kebab paths/selectors.
            (re.compile(r"sample(?=[A-Z])"), self.camel),
            (re.compile(r"sample"), self.base),
        ]

    def apply(self, text: str) -> str:
        for pattern, repl in self.replacements():
            text = pattern.sub(lambda _m, r=repl: r, text)
        return text

    def apply_line(self, line: str) -> str:
        return line if BASE64_MARKER in line else self.apply(line)


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return False
    try:
        with path.open("rb") as handle:
            chunk = handle.read(8192)
    except OSError:
        return False
    if b"\0" in chunk:
        return False
    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def walk(root: Path):
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        yield path


def git_mv(root: Path, src: Path, dst: Path) -> None:
    result = subprocess.run(
        ["git", "mv", str(src.relative_to(root)), str(dst.relative_to(root))],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        src.rename(dst)


def rename_paths(root: Path, names: Names, dry_run: bool) -> list[tuple[str, str]]:
    renamed: list[tuple[str, str]] = []
    # Deepest first so parent renames never invalidate queued child paths.
    for path in sorted(walk(root), key=lambda p: len(p.parts), reverse=True):
        new_name = names.apply(path.name)
        if new_name == path.name:
            continue
        target = path.with_name(new_name)
        renamed.append((str(path.relative_to(root)), str(target.relative_to(root))))
        if not dry_run:
            if target.exists():
                sys.exit(f"refusing to overwrite existing path: {target}")
            git_mv(root, path, target)
    return renamed


def rewrite_contents(root: Path, names: Names, dry_run: bool) -> list[str]:
    changed: list[str] = []
    for path in walk(root):
        if not path.is_file() or not is_text_file(path):
            continue
        original = path.read_text(encoding="utf-8")
        updated = "".join(names.apply_line(line) for line in original.splitlines(keepends=True))
        if updated == original:
            continue
        changed.append(str(path.relative_to(root)))
        if not dry_run:
            path.write_text(updated, encoding="utf-8")
    return changed


def read_current_version(root: Path) -> str | None:
    props = root / "backend" / "plugin" / "plugin.properties"
    if not props.exists():
        return None
    match = re.search(r"^pluginVersion=(.+)$", props.read_text(encoding="utf-8"), re.M)
    return match.group(1).strip() if match else None


def sub_in_file(root: Path, rel: str, pattern: str, repl: str, dry_run: bool, count: int = 0) -> bool:
    path = root / rel
    if not path.exists():
        return False
    original = path.read_text(encoding="utf-8")
    updated = re.sub(pattern, repl, original, count=count, flags=re.M)
    if updated == original:
        return False
    if not dry_run:
        path.write_text(updated, encoding="utf-8")
    return True


def set_version(root: Path, old: str | None, new: str, dry_run: bool) -> list[str]:
    touched: list[str] = []
    targets = [
        ("gradle.properties", r"^projectVersion=.*$", f"projectVersion={new}", 0),
        ("backend/plugin/plugin.properties", r"^pluginVersion=.*$", f"pluginVersion={new}", 0),
        (
            "frontend/projects/plugin/package.json",
            r'("version"\s*:\s*")[^"]*(")',
            rf"\g<1>{new}\g<2>",
            1,
        ),
    ]
    if old and old != new:
        # Dependency snippets in the docs and the release-notes heading.
        targets.append(("documentation/plugin.md", re.escape(old), new, 0))
        targets.append(("documentation/release-notes.md", rf"^## {re.escape(old)}$", f"## {new}", 0))
    for rel, pattern, repl, count in targets:
        if sub_in_file(root, rel, pattern, repl, dry_run, count):
            touched.append(rel)
    return touched


def leftovers(root: Path) -> list[str]:
    hits: list[str] = []
    pattern = re.compile(r"sample|gzac-plugin-template", re.I)
    for path in walk(root):
        if not path.is_file() or not is_text_file(path):
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if BASE64_MARKER in line:
                continue
            if pattern.search(line):
                hits.append(f"{path.relative_to(root)}:{lineno}: {line.strip()[:120]}")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--artifact", required=True, help="plugin artifact id, kebab-case, e.g. brp-plugin")
    parser.add_argument("--project", required=True, help="Gradle/repo project name, kebab-case")
    parser.add_argument("--version", required=True, help="initial version, e.g. 0.1.0")
    parser.add_argument("--title", help='human-readable plugin title (default: "Brp Plugin")')
    parser.add_argument("--repo-root", default=".", help="template checkout to rename (default: cwd)")
    parser.add_argument("--dry-run", action="store_true", help="report planned changes without writing")
    parser.add_argument("--force", action="store_true", help="run even if the scaffold looks already renamed")
    args = parser.parse_args()

    for label, value in (("artifact", args.artifact), ("project", args.project)):
        if not KEBAB_RE.match(value):
            return fail(f"--{label} must be lowercase kebab-case (got {value!r})")
    if not SEMVER_RE.match(args.version):
        return fail(f"--version must look like 1.2.3 (got {args.version!r})")

    root = Path(args.repo_root).resolve()
    if not (root / "backend" / "plugin" / "plugin.properties").exists():
        return fail(f"{root} does not look like a gzac-plugin-template checkout")
    sample_dir = root / "backend/plugin/src/main/kotlin/com/ritense/valtimoplugins/sampleplugin"
    if not sample_dir.exists() and not args.force:
        return fail("sample plugin sources not found -- already renamed? re-run with --force to proceed anyway")

    names = Names(args.artifact, args.project, args.title)
    old_version = read_current_version(root)

    print(f"artifact      {names.artifact}")
    print(f"project       {names.project}")
    print(f"version       {old_version or '?'} -> {args.version}")
    print(f"package       com.ritense.valtimoplugins.{names.package}")
    print(f"class prefix  {names.pascal}")
    print(f"npm package   @valtimo-plugins/{names.artifact}")
    print(f"plugin title  {names.title}")
    print()

    renamed = rename_paths(root, names, args.dry_run)
    changed = rewrite_contents(root, names, args.dry_run)
    versioned = set_version(root, old_version, args.version, args.dry_run)

    print(f"renamed paths ({len(renamed)}):")
    for src, dst in renamed:
        print(f"  {src} -> {dst}")
    print(f"\nrewrote contents ({len(changed)} files):")
    for rel in changed:
        print(f"  {rel}")
    print(f"\nversion set in ({len(versioned)}):")
    for rel in versioned:
        print(f"  {rel}")

    if args.dry_run:
        print("\ndry run -- nothing written")
        return 0

    remaining = leftovers(root)
    if remaining:
        print(f"\nWARNING: {len(remaining)} lines still mention sample/gzac-plugin-template:")
        for hit in remaining:
            print(f"  {hit}")
    else:
        print("\nno leftover template names")
    return 0


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())